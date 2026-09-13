from datetime import date

class Task:
    def __init__(self, id, title, priority = "Medium", due_date=None, completed=False):
        self.id = id
        self.title = title
        self.priority = priority
        self.due_date = due_date
        self.completed = completed

    def mark_completed(self):
        self.completed = True

    def is_overdue(self):
        if self.completed or self.due_date is None:
            return False
        else:
            return self.due_date < date.today()

    def __repr__(self):
        status = "✅" if self.completed else "❌"
        return (
            f"[{status}] {self.title} (priority={self.priority}, due={self.due_date})"
        )


task1 = Task(1, "Read Python", priority="High", due_date = date(2026, 9, 20), completed = False)
task2 = Task(
    2, "Read AI", priority="High", due_date=None, completed=False
)
task3 = Task(3, "Read AI", priority="High", due_date=date(2026,9,10), completed=False)

task_list = [task1, task2, task3]
print(task_list)
task2.mark_completed()
print(task_list)
print(task2.is_overdue())
