class Course:
    def __init__(self, id, name, price, teacher, duration, seats_count, description=None):
        self.id = id
        self.name = name
        self.price = price
        self.teacher = teacher
        self.duration = duration
        self.seats_count = seats_count
        self.description = description
        self.enrolled_count = 0
        
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "teacher": self.teacher,
            "duration": self.duration,
            "seats_count": self.seats_count
        }