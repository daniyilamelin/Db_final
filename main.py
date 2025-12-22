from turtle import title
from flask import Flask, request, render_template
import psycopg2
from datetime import datetime

app = Flask(__name__)

def get_db():
    conn = psycopg2.connect(
        host="localhost",
        database="mydb",
        user="Asus",
        password="asus",  
        port=5432
    )
    print("Підключено до бази:", conn.get_dsn_parameters())
    return conn

@app.cli.command("init_db")
def init_db_command():
    """Ініціалізація бази: створює таблиці з schema.sql"""
    with get_db() as conn:
        with conn.cursor() as cur:
            with open('schema.sql', 'r', encoding='utf-8') as f:
                sql_text = f.read()
                cur.execute(sql_text)
        conn.commit()
    print("База успішно ініціалізована ✅")

@app.cli.command("test")
def init_db():
    """Clear existing data and create new tables."""
    conn = get_db()
    cur = conn.cursor()
    with open("test.sql") as file:
        alltext = file.read() 
        cur.execute(alltext) 
    conn.commit()
    print("Initialized the database and cleared tables.")


### Routes
@app.route('/')
def index():
    return render_template('head.html')

@app.route('/browse')
def browse():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, date, hard FROM Tasks ORDER BY date')
    rows = cursor.fetchall()

    formatted_rows = []
    for row in rows:
        id_, title, date_value, hard = row
        if isinstance(date_value, datetime):
            date_str = date_value.strftime('%d/%m/%Y')
        else:
            date_str = str(date_value)
        formatted_rows.append((id_, title, date_str, hard))

    cursor.execute('SELECT COUNT(*) FROM Tasks')
    total_tasks = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return render_template('browse.html', entries=formatted_rows, total_tasks=total_tasks)



@app.route('/add_task', methods=['GET', 'POST'])
def add_task():
    message = ""
    if request.method == 'POST':
        title = request.form.get('title')
        date_str = request.form.get('date')
        hard = request.form.get('hard')

        date_obj = None
        if date_str:
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                message = "Invalid date format! Use YYYY-MM-DD."
                return render_template('add_task.html', message=message)

        conn = get_db()
        try:
            with conn.cursor() as cursor:
                
                cursor.execute("SELECT COALESCE(MAX(task_number), 0) FROM Tasks")
                max_task_number = cursor.fetchone()[0]
                new_task_number = max_task_number + 1

                cursor.execute(
                    'INSERT INTO Tasks (title, date, hard, task_number) VALUES (%s, %s, %s, %s) RETURNING id',
                    (title, date_obj, hard, new_task_number)
                )
                task_id = cursor.fetchone()[0]

                cursor.execute(
                    "INSERT INTO Step_tasks (task_id, title, something_about, hard) VALUES (%s, %s, %s, %s)",
                    (task_id, "Initial step", "Initial step", 0)
                )

            conn.commit()
            message = "Task and first step added successfully!"
        except psycopg2.Error as e:
            conn.rollback() 
            message = f"Database error: {e}"
        finally:
            conn.close()

    return render_template('add_task.html', message=message)


@app.route('/delete_task', methods=['GET', 'POST'])
def delete_task():
    message = ""
    if request.method == 'POST':
        task_id = request.form.get('ID')
        
        if not task_id or not task_id.isdigit():
            message = "Uncorrect ID!"
            return render_template('delete_task.html', message=message)
        
        task_id = int(task_id)

        conn = get_db()
        try:
            with conn.cursor() as cursor:
              
                cursor.execute("SELECT COUNT(*) FROM Tasks WHERE id = %s", (task_id,))
                exists = cursor.fetchone()[0]

                if exists == 0:
                    message = f"Task with ID {task_id} doesn`t exist."
                else:
                    cursor.execute("DELETE FROM Tasks WHERE id = %s", (task_id,))
                    conn.commit()
                    message = f"Task with ID {task_id} successfully deleted!"
        except psycopg2.Error as e:
            conn.rollback()
            message = f"Database error: {e}"
        finally:
            conn.close()

    return render_template('delete_task.html', message=message)



@app.route('/work_with_one', methods=['GET', 'POST'])
def work_with_one():
    task = None
    steps = []
    message = ""
    edit_message = ""  

    if request.method == 'POST':
        task_id = request.form.get('ID') or request.form.get('task_id')
        conn = get_db()
        try:
            with conn.cursor() as cursor:
                # Отримуємо таск
                cursor.execute("SELECT id, title, date, hard FROM Tasks WHERE id = %s", (task_id,))
                row = cursor.fetchone()
                if row:
                    formatted_date = row[2].strftime('%d-%m-%Y') if row[2] else None
                    task = (row[0], row[1], formatted_date, row[3])
                else:
                    message = "Task not found."

                if 'add_step' in request.form:
                    title = request.form.get('title')
                    something_about = request.form.get('something_about')
                    hard = request.form.get('hard')
                    cursor.execute(
                        "INSERT INTO Step_tasks (task_id, title, something_about, hard) VALUES (%s, %s, %s, %s)",
                        (task_id, title, something_about, hard)
                    )
                    step_number = +1
                    conn.commit()
                    message = "Step added successfully!"

                if "edit_task" in request.form:
                    title = request.form.get("title")
                    date = request.form.get("date")
                    hard = request.form.get("hard")
                    cursor.execute(
                        "UPDATE Tasks SET title=%s, date=%s, hard=%s WHERE id=%s",
                        (title, date, hard, task_id)
                    )
                    conn.commit()
                    edit_message = "Task updated successfully."


                if 'edit_step' in request.form:
                    step_id = request.form.get('step_id')
                    title = request.form.get('title')
                    something_about = request.form.get('something_about')
                    hard = request.form.get('hard')

                    cursor.execute(
                        "UPDATE Step_tasks SET title=%s, something_about=%s, hard=%s WHERE step_id=%s",
                        (title, something_about, hard, task_id)
                    )
                    conn.commit()
                    message = "Step updated successfully."

                if 'delete_step' in request.form:
                    step_id = request.form.get('ID')
                    cursor.execute(
                        "DELETE FROM Step_tasks WHERE step_id=%s",
                        (step_id,)
                    )
                    conn.commit()
                    message = "Step deleted successfully."

                if task:
                    cursor.execute("SELECT * FROM Step_tasks WHERE task_id = %s ORDER BY step_id", (task[0],))
                    steps = cursor.fetchall()
        except Exception as e:
            message = f"Database error: {e}"
        finally:
            conn.close()

    return render_template(
        "work_with_one.html",
        task=task,
        steps=steps,
        message=message,
        edit_message=edit_message
    )






### Start flask
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)