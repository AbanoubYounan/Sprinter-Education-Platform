'use client';
import { useAuthModal } from '@/context/AuthModalContext';
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Card, CardContent, CardActions } from '@mui/material';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Rating from '@mui/material/Rating';
import Image from 'next/image';

interface Course {
  course_ID: string;
  course_title: string;
  category: string;
  instructor_name: string;
  thumbnail_url: string;
  price: number;
  average_rating: number;
  review_count: number;
  enrollment_status: 'Active' | 'Completed' | 'Not Enrolled';
}

const CoursesList = () => {
    const [courses, setCourses] = useState<Course[]>([]);
    const [loading, setLoading] = useState(true);
    const { openModal } = useAuthModal();

    const Enroll = async (course:any) => {
        const token = localStorage.getItem('token');

        if (!token) {
            openModal('login');
            return;
        }

        // If not enrolled, make the enroll request
        if (course.enrollment_status === 'Not Enrolled') {
            try {
                const response = await axios.put(
                    "http://127.0.0.1:5000/api/courses/enroll",
                    { "CourseID": course.course_ID},
                    {
                        headers: {
                        Authorization: `${token}`
                        }
                    }
                );

                alert(response.data.Message || "Enrolled successfully!");

                // Optionally update the course status here (e.g., via useState or refetch)
                // setCourseStatus('Enrolled');

            } catch (error: any) {
                const message = error?.response?.data?.Message || "Enrollment failed";
                alert(message);
                console.error("Enrollment error:", error);
            }
        } else {
            // Already enrolled — maybe redirect or open the course
            alert(`Opening "${course.course_title}"`);
            // router.push(`/courses/${course.CourseID}`);
        }
    }


  useEffect(() => {
    const token = localStorage.getItem('token');
  
    axios.get('http://127.0.0.1:5000/api/courses', {
      headers: token ? { Authorization: `${token}` } : {}
    })
    .then(res => {
      setCourses(res.data.courses);
      console.log('courses', res.data.courses)
      setLoading(false);
    })
    .catch(err => {
      console.error("Failed to fetch courses:", err);
      setLoading(false);
    });
  }, []);
  

  if (loading) {
    return <div className="text-center mt-10 text-lg font-semibold">Loading courses...</div>;
  }

  return (
    <div className="grid gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 p-4">
      {courses.map(course => (
        <Card key={course.course_ID} className="rounded-2xl shadow-md overflow-hidden">
            <div className="relative w-full h-48">
                <Image
                src='/courses-placeholder.svg'
                alt={course.course_title}
                fill
                className="object-cover"
                />
            </div>

            <CardContent className="space-y-2">
                <Typography variant="h6" component="h2" className="font-bold line-clamp-2">
                    {course.course_title}
                </Typography>

                <Typography variant="body2" component="p" color="text.secondary">
                    {course.category} · by {course.instructor_name}
                </Typography>

                <div className="flex items-center gap-2">
                    <Rating value={course.average_rating} precision={0.1} readOnly size="small" />
                    <span className="text-sm text-gray-600">({course.review_count})</span>
                </div>

                <Typography variant="subtitle1" component="p" className="text-blue-600 font-semibold">
                    ${course.price}
                </Typography>
            </CardContent>


            <CardActions className="p-4">
                <Button
                    fullWidth
                    variant="contained"
                    color={((course.enrollment_status === 'Not Enrolled') || (!localStorage.getItem('token'))) ? 'primary' : 'success'}
                    onClick={() => {
                        const token = localStorage.getItem('token');
                        if (!token) {
                            openModal('login');
                            return;
                        }
                        if(course.enrollment_status === 'Not Enrolled'){
                            Enroll(course)
                        }else{
                            alert(`Opening "${course.course_title}"`)
                        }
                    }}
                    >
                    {((course.enrollment_status === 'Not Enrolled') || (!localStorage.getItem('token'))) ? 'Enroll' : 'Open Course'}
                </Button>
            </CardActions>
        </Card>
      ))}
    </div>
  );
};

export default CoursesList;
