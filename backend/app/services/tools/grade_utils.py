grade_to_score = {'S':6, 'A':5, 'B':4, 'C':3, 'D':2, 'E':1, 'F':0}
score_to_grade = {v: k for k, v in grade_to_score.items()}

def map_grade_to_score(grade):
    return grade_to_score.get(grade, 0)

def map_score_to_grade(score):
    rounded = round(score)
    return score_to_grade.get(rounded, '에러')