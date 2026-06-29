def predict_risk(
    temp,
    water,
    dizziness,
    headache,
    bmi
):

    score = 0

    if temp >= 42:
        score += 3

    elif temp >= 38:
        score += 2

    if water < 2:
        score += 2

    if dizziness == 1:
        score += 1

    if headache == 1:
        score += 1

    if bmi >= 30:
        score += 1

    if score >= 6:
        return "HIGH"

    elif score >= 3:
        return "MEDIUM"

    else:
        return "LOW"