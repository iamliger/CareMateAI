from django.db import models
from django.contrib.auth.models import User
from datetime import date


# 1. 게시판 카테고리
class Category(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


# 2. 커뮤니티 게시글 (이미지 보안 포함)
class Post(models.Model):
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="posts"
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to="post_images/", null=True, blank=True)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )
    is_secret = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, related_name="liked_posts", blank=True)
    dislikes = models.ManyToManyField(User, related_name="disliked_posts", blank=True)


# 3. 다층형 댓글
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )
    created_at = models.DateTimeField(auto_now_add=True)


# 4. 건강 프로필 (응급 카드 + 신원 정보)
class HealthProfile(models.Model):
    BLOOD_TYPES = [
        ("미설정", "미설정"),
        ("A+", "A+"),
        ("A-", "A-"),
        ("B+", "B+"),
        ("B-", "B-"),
        ("O+", "O+"),
        ("O-", "O-"),
        ("AB+", "AB+"),
        ("AB-", "AB-"),
    ]
    GENDER_CHOICES = [("M", "남성"), ("F", "여성"), ("U", "미설정")]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="health")
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default="U")
    phone_number = models.CharField(max_length=20, blank=True)
    height = models.FloatField(default=0.0)
    weight = models.FloatField(default=0.0)
    blood_type = models.CharField(max_length=5, choices=BLOOD_TYPES, default="미설정")
    chronic_diseases = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=20, blank=True)
    is_pregnant = models.BooleanField(default=False)
    expected_due_date = models.DateField(null=True, blank=True)
    is_smoking = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def get_international_age(self):
        if not self.birth_date:
            return "미설정"
        today = date.today()
        return (
            today.year
            - self.birth_date.year
            - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        )


# 5. 일일 정밀 건강/식단 로그
class DailyLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="daily_logs")
    date = models.DateField(auto_now_add=True)
    weight = models.FloatField(default=0.0)
    height = models.FloatField(default=0.0)
    bp_systolic = models.IntegerField(default=0)
    bp_diastolic = models.IntegerField(default=0)
    steps = models.IntegerField(default=0)
    sleep_hours = models.FloatField(default=0.0)
    stress_level = models.IntegerField(default=5)
    water_ml = models.IntegerField(default=0)
    alcohol_cups = models.IntegerField(default=0)
    smoking_sticks = models.IntegerField(default=0)
    breakfast = models.CharField(max_length=200, blank=True)
    lunch = models.CharField(max_length=200, blank=True)
    dinner = models.CharField(max_length=200, blank=True)
    memo = models.TextField(blank=True)

    class Meta:
        unique_together = ("user", "date")
        ordering = ["-date"]


# 6. 실시간 흡연 타임라인 로그
class SmokingLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="smoke_times")
    smoked_at = models.DateTimeField(auto_now_add=True)
    date = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ["-smoked_at"]


# 7. 복약 관리
class Medication(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="medications")
    name = models.CharField(max_length=100)
    dosage = models.CharField(max_length=100, blank=True, default="")
    time_to_take = models.TimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


# 8. 복구 상담 기록
class BehaviorLog(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="recovery_logs"
    )
    event_type = models.CharField(max_length=20)
    description = models.TextField()
    ai_advice = models.TextField(blank=True)
    expert_tip = models.TextField(blank=True)
    recommended_food = models.CharField(max_length=100, blank=True)
    shop_url = models.URLField(blank=True)
    is_hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


# 9. 레시피 및 통계
class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="recipes", null=True, blank=True
    )
    title = models.CharField(max_length=100)
    ingredients = models.TextField()
    instructions = models.TextField()
    calories = models.IntegerField(default=0)
    image = models.ImageField(upload_to="recipes/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class VisitorLog(models.Model):
    ip = models.GenericIPAddressField()
    user_agent = models.TextField()
    visited_at = models.DateField(auto_now_add=True)
