from flask import Flask, redirect, render_template, request, session, url_for, Response, send_file
import os
import io
import sqlite3 as sl
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.linear_model import LinearRegression
import datetime

# sets up Flask
app = Flask(__name__)
db = "food.db"


@app.route("/")
def home():
    return render_template("pantry.html")


@app.route("/pantry_output", methods=['POST'])
def pantry():
    # connect to the database
    conn = sl.connect(db)
    curs = conn.cursor()

    # selects everything from the table of the stock that the user chose

    stmt = "SELECT * FROM RECIPES"

    userItems = request.form['Required Items']
    userCals = int(request.form['Calorie Limit'])

    # converts the database data into a DataFrame
    calCount = []
    df = pd.read_sql(stmt, conn)
    for index,row in df.iterrows():
        calRow = row["nutrition"].strip('[]')
        nutritionFacts = calRow.split(',')
        nutritionFacts[0] = nutritionFacts[0].strip('\'')
        calCount.append((float)(nutritionFacts[0]))


    df['calorie_match'] = calCount




    importantPantry = userItems.split(",")

    dfSplit = df[df['calorie_match'] >= 0.75 * userCals]
    dfSplit = dfSplit[dfSplit['calorie_match'] <= 1.25 * userCals]
    dfPantry = create_recipe_dataframe(importantPantry, dfSplit, userCals)

    # shows the best matching recipes and their information (calories, nutrition, difficulty) and saves it

    # dfIngredientSort = df.sort_values(by=['same_match'])

    dfPantry['final_index'] = dfPantry['cal_index'] *.3 + dfPantry['same_match'] * .7
    dfPantry = dfPantry.sort_values(by=['final_index'], ascending=False)

    dfPantry = dfPantry.iloc[:20,:]

    #name, calories, ingredients, difficulty
    recipesArray = data_into_object(dfPantry)


    testRes = ["Lasagna", "Grilled Cheese", "Tacos"]
    testCal = [700, 700, 700]
    testIngr = []
    return render_template("pantry_output.html", recipes=recipesArray) #, testRes=testRes, testCal=testCal, testIngr=testIngr)

    # will render a new template displaying the output data

# uses SQL queries to make a dataframe of the ingredients for each recipe
def create_recipe_dataframe(pantry, df, cals):

    numSameList = []
    cal_index = []
    difficultyList = []
    rating_list = []
    # recipeDF = df["ingredients"]
    for index,row in df.iterrows():
        ingRow = row["ingredients"].strip('[]')
        ingredientList = ingRow.split(',')
        ingredientList = [item.strip() for item in ingredientList]
        ingredientList = [item.strip('\'') for item in ingredientList]
        numSameList.append(is_valid_recipe(ingredientList, pantry) / len(ingredientList))

        if row["n_steps"] >= 10:
            if row["minutes"] >= 60:
                difficultyList.append("Hard")
            else:
                difficultyList.append("Medium")
        else:
            if row["minutes"] >= 60:
                difficultyList.append("Medium")
            else:
                difficultyList.append("Easy")

        #percent difference * 4
        cal_index.append(1 - ((abs((float(row["calorie_match"]) - float(cals))) / float(cals)) * 4))
        #rating_list.append(1)

    # if no entered ingredients, make all recipes valid?
    # make column for other compatible ingredients? -> slower runtime
    df['same_match'] = numSameList

    # cal_list = cal_goal(cals, df)
    # df['calorie_match'] = calCount

    #difficulty_list = rateDifficulty(df)
    df['difficulty'] = difficultyList

    #rating_list = rateDishes(df)
    #df['rating'] = rating_list

    df['cal_index'] = cal_index

    dfSplitIng = df[df['same_match'] > 0]

    return dfSplitIng


# finds if a recipe is valid based on ingredients and pantry
# returns index of how closely it matches the ingredient, ex: 0.94 match
def is_valid_recipe(ingredientArray, pantry):
    # first filter based on necessary ingredients
    count = 0
    for i in pantry:
        for j in ingredientArray:
        # check if all elements in importantPantry are found in ingredientArray
        # must use have ex: 'beef' should get 'ground beef'
            if i in j:
                # return the match number
                count += 1

    return count

# returns array of recipe objects
def data_into_object(df):
    recipes = []
    for index,row in df.iterrows():
        row["ingredients"] = row["ingredients"].strip("[]")
        ingredientList = row["ingredients"].split(',')
        ingredientList = [item.strip() for item in ingredientList]
        ingredientList = [item.strip('\'') for item in ingredientList]
        ingredientList = [item.strip('\"') for item in ingredientList]
        ingredientString = ", ".join(ingredientList)

        recipe = Recipe(row["name"], row["calorie_match"], ingredientString, row["difficulty"], round(row["final_index"] * 100))
        recipes.append(recipe)
    return recipes

# user class that holds name, pantry items, and recipes that they saved
class user:
    def __init__(self, username, pantry, cal_goals, saved_recipes):
        self.username = username
        self.pantry = pantry
        self.cal_goals = cal_goals
        self.saved_recipes = saved_recipes

    def save_recipe(self):
        print()

    def update_pantry(self):
        print()

    def update_cal_goals(self, cals):
        #first update the cal goals
        self.cal_goals = cals
        #update the dataframe values for cals

# recipe object
class Recipe:
    def __init__(self, name, calories, ingredients, difficulty, match):
        self.name = name
        self.calories = calories
        self.ingredients = ingredients
        self.difficulty = difficulty
        self.match = match

    def food(self):
        return self.name

    def calNum(self):
        return self.calories
    
    def ingList(self):
        return self.ingredients

    def difficulty(self):
        return self.difficulty

    def match(self):
        return self.match

if __name__ == "__main__":
    # sets a secret key and runs with a debugger
    app.secret_key = os.urandom(5)
    app.run(debug=True)
