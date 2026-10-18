import csv
import random

random.seed(42)

with open("students.csv", "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)

    writer.writerow([
        "english",
        "mathematics",
        "science",
        "social_studies",
        "attendance",
        "study_hours"
    ])

    for _ in range(1000):
        study_hours = round(random.uniform(0, 6), 1)
        attendance = round(random.uniform(55, 100), 1)
        ability = random.gauss(65, 13)

        improvement = (
            (study_hours / 6) * 10
            + ((attendance - 55) / 45) * 8
        )

        marks = []

        for difficulty in [0, -4, 2, -1]:
            score = (
                ability
                + improvement
                + difficulty
                + random.gauss(0, 9)
            )

            score = max(0, min(100, score))
            marks.append(round(score, 1))

        writer.writerow(
            marks + [attendance, study_hours]
        )

print("Dataset generated successfully: 1000 students")
