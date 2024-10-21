from flask import Blueprint, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import User, Subscription, SubscriptionTier, db
from datetime import datetime, timedelta

subscription_bp = Blueprint('subscription_bp', __name__)

def create_or_update_subscription(user_id, tier, billing_cycle='monthly'):
    user = User.query.get(user_id)
    if not user:
        return False, "User not found"

    limits = {
        SubscriptionTier.STARTER.value: {"max_projects": 1, "max_respondents_per_survey": 100, "max_interactions_per_month": 500},
        SubscriptionTier.ADVANCED.value: {"max_projects": 1000, "max_respondents_per_survey": 500, "max_interactions_per_month": 10000},
        SubscriptionTier.ENTERPRISE.value: {"max_projects": 10000, "max_respondents_per_survey": 1000000, "max_interactions_per_month": 10000000},
    }

    duration = timedelta(days=365 if billing_cycle == 'yearly' else 30)

    if user.subscription:
        subscription = user.subscription
        action = "updated"
    else:
        subscription = Subscription(user_id=user_id)
        db.session.add(subscription)
        action = "created"

    subscription.tier = tier
    subscription.start_date = datetime.utcnow()
    subscription.end_date = datetime.utcnow() + duration
    subscription.is_active = True
    subscription.max_projects = limits[tier]['max_projects']
    subscription.max_respondents_per_survey = limits[tier]['max_respondents_per_survey']
    subscription.max_interactions_per_month = limits[tier]['max_interactions_per_month']
    subscription.remaining_interactions = limits[tier]['max_interactions_per_month']

    db.session.commit()
    return True, f"{tier} subscription {action} successfully"

@subscription_bp.route('/set_subscription', methods=['POST'])
@login_required
def set_subscription():
    tier = request.form.get('tier')
    billing_cycle = request.form.get('billing_cycle', 'monthly')
    
    if tier not in [t.value for t in SubscriptionTier]:
        flash('Invalid subscription tier.', 'danger')
        return redirect(url_for('pricing'))

    success, message = create_or_update_subscription(current_user.id, tier, billing_cycle)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    return redirect(url_for('pricing'))

@subscription_bp.route('/cancel_subscription', methods=['POST'])
@login_required
def cancel_subscription():
    if current_user.subscription:
        db.session.delete(current_user.subscription)
        db.session.commit()
        flash("Subscription cancelled successfully", 'success')
    else:
        flash("No active subscription to cancel", 'warning')
    return redirect(url_for('pricing'))

# You can keep the stripe_webhook route if you're planning to use Stripe in the future
@subscription_bp.route('/stripe_webhook', methods=['POST'])
def stripe_webhook():
    # Placeholder for future Stripe integration
    return "Webhook received", 200