from profile_model import ProfileModel
from sqlalchemy import and_, or_, between, func
from datetime import datetime

class Filter:
    def __init__(self, tags=None, gender=None, age_interval=None, location=None, education_level=None, occupation=None,
                 income_range=None, ethnicity=None, religion=None, health_status=None, legal_status=None, 
                 marital_status=None, hobbies=None, mbti_profile=None):
        self.tags = tags or []  # List of tags
        self.gender = gender or []  # List of genders
        self.age_interval = age_interval  # Tuple (min_age, max_age)
        self.location = location
        self.education_level = education_level
        self.occupation = occupation or []
        self.income_range = income_range or []
        self.ethnicity = ethnicity or []
        self.religion = religion or []
        self.health_status = health_status or []
        self.legal_status = legal_status or []
        self.marital_status = marital_status or []
        self.hobbies = hobbies or []
        self.mbti_profile = mbti_profile or []

    def apply_filters(self, query):
        # If any filters are applied, modify the query accordingly.
        if self.tags:
            query = query.filter(ProfileModel.tags.ilike(f"%{self.tags}%"))

        if self.gender:
            query = query.filter(ProfileModel.gender.in_(self.gender))

        if self.age_interval:
            min_date = datetime.now().date().replace(year=datetime.now().year - self.age_interval[1])
            max_date = datetime.now().date().replace(year=datetime.now().year - self.age_interval[0])
            query = query.filter(ProfileModel.birth_date.between(min_date, max_date))

        if self.location:
            query = query.filter(ProfileModel.location.ilike(f"%{self.location}%"))

        if self.education_level:
            query = query.filter(ProfileModel.education_level.ilike(f"%{self.education_level}%"))

        if self.occupation:
            query = query.filter(ProfileModel.occupation.in_(self.occupation))

        if self.income_range:
            query = query.filter(ProfileModel.income_range.in_(self.income_range))

        if self.ethnicity:
            query = query.filter(ProfileModel.ethnicity.in_(self.ethnicity))

        if self.religion:
            query = query.filter(ProfileModel.religion.in_(self.religion))

        if self.health_status:
            query = query.filter(ProfileModel.health_status.in_(self.health_status))

        if self.legal_status:
            query = query.filter(ProfileModel.legal_status.in_(self.legal_status))

        if self.marital_status:
            query = query.filter(ProfileModel.marital_status.in_(self.marital_status))

        # Apply hobbies filtering using ILIKE for partial matching
        if self.hobbies:
            for hobby in self.hobbies:
                query = query.filter(ProfileModel.hobbies.ilike(f'%{hobby}%'))

        if self.mbti_profile:
            query = query.filter(ProfileModel.mbti_profile.in_(self.mbti_profile))

        # Return the filtered query
        return query
