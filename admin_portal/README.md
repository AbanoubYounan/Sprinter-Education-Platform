
# 📚 Sprints Admin Panel

Welcome to the **Sprints Admin Panel**, a powerful and user-friendly web interface for managing users, courses, chapters, enrollment, and tracking student progress in a structured educational system.

---

## 🚀 Features

- 👤 **User Management**: View, add, edit, and manage user details.
- 📘 **Course Management**: Full CRUD operations for courses.
- 📂 **Chapter Management**: Add, edit, and view course chapters.
- 📝 **Student Enrollment**: Handle student enrollments per course.
- 📊 **Course Progress Tracker**: Track students' progress throughout the course.
- 📈 **Dashboard**: Visualize student progress and insights.

---

## 🧰 Tech Stack

- **Python 3.8+**
- **Streamlit**
- **MySQL**
- Modular structure for scalability and maintainability

---

## 🖼️ Screenshots

![Admin Panel Screenshot](assets/sprints_logo.png)

---

## 🛠️ Setup Instructions

1. **Clone the repository**

```bash
git https://github.com/AbanoubYounan/Sprinter-Education-Platform.git
cd admin_portal
```

2. **Create virtual environment (optional but recommended)**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Set up your MySQL database** and update the connection in `db_connection.py`.

5. **Run the application**

```bash
streamlit run main.py
```

---

## 🧱 Project Structure

```
├── assets/
│   └── sprints_logo.png
|   └── Users_Page
|   └── Courses_Page
|   └── Chapters_Page
|   └── Enrollment_Page
|   └── Course_Progress_Tracker
|   └── Dashboard_Page
|
├── app.py
├── db_connection.py
├── user_modules/
├── course_modules/
├── chapter_modules/
├── content_modules/
├── student_progress_module/
├── student_enrollment_module/
├── Course_Progress_Tracker_module/
└── requirements.txt
```

---

## 👨‍💻 Developer
** Sprints Team One**
---
## 📄 License
MIT License. See `LICENSE` file for more information.

---
## 👤 Home Page Schreenshoots and demo
![Users Page](assets\Users_Page\Users_Home_Page.png)

![Add User](assets\Users_Page\Add_User.png) 
![Edit User](assets\Users_Page\Edit_User.png) 
![Show User](assets\Users_Page\Show_User.png) 
![Watch User Demo Video](assets\Users_Page\User_Page_Demo.mp4) 
---
## 📘 Courses Page Schreenshoots and demo

![Course Page](assets\Courses_Page\Course_Home_Page.png)

![Add Course](assets\Courses_Page\Add_Course.png) 
![Edit Course](assets\Courses_Page\Edit_Course.png) 
![Show Course](assets\Courses_Page\Show_Course.png) 
![Watch Course Demo Video](assets\Courses_Page\Course_Page_Demo.mp4) 

---
## 📂 Chapters Page Schreenshoots and demo

![Chapter Page](assets/Chapters_Page/Chapters_Home_Page.png)

![Chapter Per course](assets\Chapters_Page\Chapter_Per_Course.png) 
![Lesson Per Chapter](assets\Chapters_Page\Lessons_Per_Chapter.png) 
![Edit Chapter](assets\Chapters_Page\Edit_Chapter.png) 
![Edit Lesson](assets\Chapters_Page\Edit_Content_Details.png) 
![Watch Chapter Demo Video](assets\Chapters_Page\Chapter_Page_Demo.mp4) 
---
## 📝 Enrollment Page Schreenshoots and demo

![Enrollment Home Page](assets\Enrollment_Page\Enrollment_Home_Page.png)

![Enrollment Per User](assets\Enrollment_Page\Enrollment_Per_User.png) 
![Lesson Per Chapter](assets\Chapters_Page\Lessons_Per_Chapter.png) 
![Instructor Courses](assets\Enrollment_Page\Instructor_Courses.png) 
![Course Per Instructor](assets\Enrollment_Page\Course_Per_Instructor.png) 
![Watch Chapter Enrollment Video](assets\Enrollment_Page\Enrollment_Page_Demo.mp4) 

---
## 📊 Course Progress Tracker Page Schreenshoots and demo
![Course Progress Tracker Home Page](assets\Course_Progress_Tracker\Course_Progress_Tracker_HomePage.png)

![Enrollment Course Progress Tracker](assets\Course_Progress_Tracker\Course_Progress_Tracker_Demo.mp4) 

---
## 📈 Dashboard Page Schreenshoots and demo
![Dashboard Home Page](assets\Dashboard_Page\ProgressManagementDashboard_HomePage.png)

![Instructor Leaderboard](assets\Dashboard_Page\InstructorLeaderBoard.png) 
![Student Leaderboard](assets\Dashboard_Page\StudentDashboard.png)
![Dashboard Demo Video](assets\Dashboard_Page\Dashboard_Demo_Video.mp4) 