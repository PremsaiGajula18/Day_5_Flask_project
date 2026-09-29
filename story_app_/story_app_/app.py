import os

import mysql.connector
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, url_for

# Read database settings from the .env file.
load_dotenv()
app = Flask(__name__)


def get_db():
    # Each database operation opens its own connection.
    return mysql.connector.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", "3306")),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
    )


def all_stories():
    connection = get_db()
    cursor = None

    try:
        # dictionary=True lets templates use names like story['title'].
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, title, author, story "
            "FROM stories ORDER BY id DESC"
        )
        # Fetch once: reading the results empties them from the cursor.
        stories = cursor.fetchall()
        print(stories)
        return stories
    finally:
        # Always close database resources, including when a query fails.
        if cursor is not None:
            cursor.close()
        connection.close()


def find_story(story_id):
    connection = get_db()
    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)
        # %s safely inserts the ID as a value instead of SQL code.
        cursor.execute(
            "SELECT id, title, author, story "
            "FROM stories WHERE id = %s",
            (story_id,),
        )
        story = cursor.fetchone()
        print(story)
        return story
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


def save_story(title, author, story):
    connection = get_db()
    cursor = None

    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO stories (title, author, story) "
            "VALUES (%s, %s, %s)",
            (title, author, story),
        )
        # Save the change permanently in the database.
        print("Saving story:", title, author, story)
        connection.commit()
    except Exception:
        # Undo the change if saving fails, then show the original error.
        connection.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


def remove_story(story_id):
    connection = get_db()
    cursor = None

    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM stories WHERE id = %s", (story_id,))
        connection.commit()
        print("Deleted story with ID:", story_id)
    except Exception:
        connection.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


@app.route("/", methods=["GET", "POST"])
def home():
    """Show all stories and handle the form that adds a story."""
    if request.method == "POST":
        # Read form fields and trim accidental spaces at the ends.
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        story = request.form.get("story", "").strip()

        if not title or not author or not story:
            return render_template(
                "home.html",
                stories=all_stories(),
                form=request.form,
                error="Please fill in all fields.",
            ), 400

        save_story(title, author, story)
        # Redirect after saving so refreshing the page won't submit twice.
        print("Redirecting to home after saving story.")
        return redirect(url_for("home"))

    return render_template(
        "home.html",
        stories=all_stories(),
        form={},
    )


@app.route("/delete/<int:story_id>", methods=["POST"])
def delete_story(story_id):
    """Delete one story, then return to the list."""
    remove_story(story_id)
    print("Redirecting to home after deleting story with ID:", story_id)
    return redirect(url_for("home"))


@app.route("/edit/<int:story_id>", methods=["GET", "POST"])
def edit_story(story_id):
    """Show the edit form on GET and save its changes on POST."""
    story = find_story(story_id)

    if story is None:
        return "Story not found", 404

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        story_text = request.form.get("story", "").strip()

        if not title or not author or not story_text:
            return render_template(
                "edit_story.html",
                form=request.form,
                error="Please fill in all fields.",
            ), 400

        connection = get_db()
        print("Updating story with ID:", story_id)
        print(connection)
        
        cursor = None

        try:
            cursor = connection.cursor()
            # Update only the selected story, using safe SQL parameters.
            cursor.execute(
                "UPDATE stories "
                "SET title = %s, author = %s, story = %s "
                "WHERE id = %s",
                (title, author, story_text, story_id),
            )
            connection.commit()
            print("Successfully updated story with ID:", story_id)
            print("New values - Title:", title, "Author:", author, "Story:", story_text)
            print(connection)
        except Exception:
            # Keep the database unchanged if the update fails.
            connection.rollback()
            raise
        finally:
            if cursor is not None:
                cursor.close()
            connection.close()

        return redirect(url_for("home"))

    return render_template("edit_story.html", form=story)


if __name__ == "__main__":
    app.run(debug=True)