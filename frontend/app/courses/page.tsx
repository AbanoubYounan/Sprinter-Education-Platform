// app/courses/page.tsx
'use client';
import CoursesList from '@/components/courses/CoursesList'; // adjust the import path as needed

const CoursesPage = () => {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Available Courses</h1>
      <CoursesList />
    </div>
  );
};

export default CoursesPage;
