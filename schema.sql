-- видаляємо залежні таблиці спочатку
DROP TABLE IF EXISTS Step_tasks CASCADE;
DROP TABLE IF EXISTS Tasks CASCADE;

-- створюємо головну таблицю
CREATE TABLE Tasks (
    id SERIAL PRIMARY KEY NOT NULL,
    title VARCHAR(80) NOT NULL,
    date TIMESTAMP WITH TIME ZONE NOT NULL,
    hard TEXT NOT NULL,
    task_number INT NOT NULL DEFAULT 0

);

-- створюємо залежну таблицю
CREATE TABLE Step_tasks (
    step_id SERIAL PRIMARY KEY NOT NULL,
    task_id INT NOT NULL REFERENCES Tasks(id) ON DELETE CASCADE,
    title VARCHAR(80) NOT NULL,
    something_about TEXT NOT NULL,
    
    hard TEXT NOT NULL
);


CREATE OR REPLACE FUNCTION update_task_count()
RETURNS TRIGGER AS $$
BEGIN
    -- Після вставки нового таску збільшуємо лічильник
    IF TG_OP = 'INSERT' THEN
        UPDATE Tasks
        SET task_number = task_number + 1
        WHERE id = NEW.id;
        RETURN NEW;
    END IF;

    -- Після видалення таску зменшуємо лічильник
    IF TG_OP = 'DELETE' THEN
        UPDATE Tasks
        SET task_number = task_number - 1
        WHERE id = OLD.id;
        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER task_count_trigger
AFTER INSERT OR DELETE ON Tasks
FOR EACH ROW
EXECUTE FUNCTION update_task_count();
