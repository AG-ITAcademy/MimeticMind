from models import ProfileModel
from sqlalchemy import and_, or_, between
from datetime import datetime

class Filter:
    def __init__(self, tags=None, gender=None, age_interval=None, location=None, education_level=None, occupation=None,
                 income_range=None, ethnicity=None, religion=None, health_status=None, legal_status=None, 
                 marital_status=None, hobbies=None, mbti_profile=None):
        self.tags = tags or []  
        self.gender = gender or []  
        self.age_interval = age_interval  
        self.location = location
        self.education_level = education_level
        self.occupation = occupation or []
        self.income_range = income_range or []
        self.ethnicity = ethnicity or []
        self.religion = religion or []
        self.health_status = health_status or []
        self.legal_status = legal_status or []
        self.marital_status = marital_status or []


    def apply_filters(self, query):
        # Ensure all fields that could be single values are converted to lists if necessary
        if self.tags:
            if isinstance(self.tags, str):
                self.tags = [self.tags]
            query = query.filter(ProfileModel.tags.ilike(f"%{self.tags}%"))

        if self.gender:
            if isinstance(self.gender, str):
                self.gender = [self.gender]
            query = query.filter(ProfileModel.gender.in_(self.gender))

        if self.age_interval:
            # Set defaults if either age_min or age_max is None
            age_min = self.age_interval[0] if self.age_interval[0] is not None else 0
            age_max = self.age_interval[1] if self.age_interval[1] is not None else 150

            # Only apply the filter if both min and max aren't None
            if not (self.age_interval[0] is None and self.age_interval[1] is None):
                min_date = datetime.now().date().replace(year=datetime.now().year - age_max)
                max_date = datetime.now().date().replace(year=datetime.now().year - age_min)
                query = query.filter(ProfileModel.birth_date.between(min_date, max_date))

        if self.location:
            if isinstance(self.location, str):
                self.location = [self.location]
            query = query.filter(or_(*[ProfileModel.location.ilike(f"%{loc}%") for loc in self.location]))

        if self.education_level:
            if isinstance(self.education_level, str):
                self.education_level = [self.education_level]
            query = query.filter(ProfileModel.education_level.in_(self.education_level))

        if self.occupation:
            if isinstance(self.occupation, str):
                self.occupation = [self.occupation]
            query = query.filter(ProfileModel.occupation.in_(self.occupation))

        if self.income_range:
            if isinstance(self.income_range, str):
                self.income_range = [self.income_range]
            query = query.filter(ProfileModel.income_range.in_(self.income_range))

        if self.ethnicity:
            if isinstance(self.ethnicity, str):
                self.ethnicity = [self.ethnicity]
            query = query.filter(ProfileModel.ethnicity.in_(self.ethnicity))

        if self.religion:
            if isinstance(self.religion, str):
                self.religion = [self.religion]
            query = query.filter(ProfileModel.religion.in_(self.religion))

        if self.health_status:
            if isinstance(self.health_status, str):
                self.health_status = [self.health_status]
            query = query.filter(ProfileModel.health_status.in_(self.health_status))

        if self.legal_status:
            if isinstance(self.legal_status, str):
                self.legal_status = [self.legal_status]
            query = query.filter(ProfileModel.legal_status.in_(self.legal_status))

        if self.marital_status:
            if isinstance(self.marital_status, str):
                self.marital_status = [self.marital_status]
            query = query.filter(ProfileModel.marital_status.in_(self.marital_status))

        return query

    def to_dict(self):
        """Converts Filter object to a dictionary for serialization."""
        return {
            'tags': self.tags,
            'gender': self.gender,
            'age_interval': self.age_interval,
            'location': self.location,
            'education_level': self.education_level,
            'occupation': self.occupation,
            'income_range': self.income_range,
            'ethnicity': self.ethnicity,
            'religion': self.religion,
            'health_status': self.health_status,
            'legal_status': self.legal_status,
            'marital_status': self.marital_status
        }

    @classmethod
    def from_dict(cls, data):
        """Creates a Filter object from a dictionary."""
        return cls(**data)

    @classmethod
    def from_model(cls, model):
        """Creates a Filter object from a FilterModel instance."""
        return cls(
            gender=model.gender,
            age_interval=(model.age_min, model.age_max),
            location=model.location,
            education_level=model.education_level,
            occupation=model.occupation,
            income_range=model.income_range,
            ethnicity=model.ethnicity,
            religion=model.religion,
            health_status=model.health_status,
            legal_status=model.legal_status,
            marital_status=model.marital_status
        )
        
