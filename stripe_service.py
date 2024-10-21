import stripe
from models import db, User, Subscription, SubscriptionTier
from config import Config
from datetime import datetime, timedelta

class StripeService:
    @staticmethod
    def create_checkout_session(user_id, tier, billing_cycle):
        stripe.api_key = Config.STRIPE_SECRET_KEY
        user = User.query.get(user_id)

        # Define your product and price IDs here
        price_id = {
            (SubscriptionTier.ADVANCED, 'monthly'): 'price_advanced_monthly',
            (SubscriptionTier.ADVANCED, 'yearly'): 'price_advanced_yearly',
            (SubscriptionTier.ENTERPRISE, 'monthly'): 'price_enterprise_monthly',
            (SubscriptionTier.ENTERPRISE, 'yearly'): 'price_enterprise_yearly',
        }.get((tier, billing_cycle))

        session = stripe.checkout.Session.create(
            customer_email=user.email,
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=Config.DOMAIN + '/subscription/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=Config.DOMAIN + '/subscription/cancel',
            client_reference_id=str(user_id),
            metadata={
                'user_id': user_id,
                'tier': tier.value,
                'billing_cycle': billing_cycle,
            }
        )

        return session.id

    @staticmethod
    def handle_webhook(payload, sig_header):
        stripe.api_key = Config.STRIPE_SECRET_KEY
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, Config.STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            return 'Invalid payload', 400
        except stripe.error.SignatureVerificationError as e:
            return 'Invalid signature', 400

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            StripeService.fulfill_subscription(session)
        elif event['type'] == 'customer.subscription.updated':
            subscription = event['data']['object']
            StripeService.update_subscription(subscription)
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            StripeService.cancel_subscription(subscription)

        return 'Success', 200

    @staticmethod
    def fulfill_subscription(session):
        user_id = int(session['client_reference_id'])
        tier = SubscriptionTier(session['metadata']['tier'])
        billing_cycle = session['metadata']['billing_cycle']
        
        user = User.query.get(user_id)
        
        # Define subscription limits based on tier
        limits = {
            SubscriptionTier.ADVANCED: {"max_projects": float('inf'), "max_respondents_per_survey": 500, "max_interactions_per_month": 10000},
            SubscriptionTier.ENTERPRISE: {"max_projects": float('inf'), "max_respondents_per_survey": float('inf'), "max_interactions_per_month": float('inf')},
        }

        end_date = datetime.utcnow() + timedelta(days=365 if billing_cycle == 'yearly' else 30)

        if user.subscription:
            user.subscription.tier = tier
            user.subscription.is_active = True
            user.subscription.start_date = datetime.utcnow()
            user.subscription.end_date = end_date
            user.subscription.max_projects = limits[tier]['max_projects']
            user.subscription.max_respondents_per_survey = limits[tier]['max_respondents_per_survey']
            user.subscription.max_interactions_per_month = limits[tier]['max_interactions_per_month']
            user.subscription.remaining_interactions = limits[tier]['max_interactions_per_month']
        else:
            new_subscription = Subscription(
                user_id=user_id,
                tier=tier,
                start_date=datetime.utcnow(),
                end_date=end_date,
                is_active=True,
                **limits[tier]
            )
            new_subscription.remaining_interactions = new_subscription.max_interactions_per_month
            db.session.add(new_subscription)
        
        db.session.commit()

    @staticmethod
    def update_subscription(stripe_subscription):
        # You'll need to map Stripe's subscription data to your Subscription model
        # This is a placeholder implementation
        user = User.query.filter_by(stripe_customer_id=stripe_subscription['customer']).first()
        if user and user.subscription:
            user.subscription.is_active = stripe_subscription['status'] == 'active'
            # Update other fields as necessary
            db.session.commit()

    @staticmethod
    def cancel_subscription(stripe_subscription):
        user = User.query.filter_by(stripe_customer_id=stripe_subscription['customer']).first()
        if user and user.subscription:
            user.subscription.is_active = False
            user.subscription.end_date = datetime.utcnow()
            db.session.commit()