/* frontend\components\courses\CoursesList.tsx*/
'use client';
/* eslint-disable  @typescript-eslint/no-explicit-any */
import { useAuthModal } from '@/context/AuthModalContext';
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Card, CardContent, CardActions } from '@mui/material';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Rating from '@mui/material/Rating';
import LinearProgress from '@mui/material/LinearProgress';
import Image from 'next/image';

const ENV_MODE = process.env.NEXT_PUBLIC_ENV_MODE;
const DEV_DOMAIN_NAME = process.env.NEXT_PUBLIC_DEV_DOMAIN_NAME;
const PRO_DOMAIN_NAME = process.env.NEXT_PUBLIC_PRO_DOMAIN_NAME;

interface Course {
  course_ID: string;
  course_title: string;
  category: string;
  instructor_name: string
  thumbnail_url: string;
  price: number;
  average_rating: number;
  review_count: number;
  enrollment_status: 'Active' | 'Completed' | 'Not Enrolled';
  my_progress: number; // ✅ New field
}

const CoursesList = () => {
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const { openModal } = useAuthModal();

  const Enroll = async (course: any) => {
    const token = localStorage.getItem('token');

    if (!token) {
      openModal('login');
      return;
    }

    if (course.enrollment_status === 'Not Enrolled') {
      try {
        const response = await axios.put(
          `${ENV_MODE === 'DEV' ? DEV_DOMAIN_NAME : PRO_DOMAIN_NAME}api/courses/enroll`,
          { CourseID: course.course_ID },
          {
            headers: {
              Authorization: `${token}`,
            },
          }
        );

        if (response.status === 201) {
          setCourses((prevCourses) =>
            prevCourses.map((c) =>
              c.course_ID === course.course_ID
                ? { ...c, enrollment_status: 'Active', my_progress: 0 }
                : c
            )
          );
        }
      } catch (error: any) {
        const message = error?.response?.data?.Message || 'Enrollment failed';
        alert(message);
        console.error('Enrollment error:', error);
      }
    } else {
      alert(`Opening "${course.course_title}"`);
    }
  };

  const fetchCourses = () => {
    const token = localStorage.getItem('token');
    axios
      .get(`${ENV_MODE === 'DEV' ? DEV_DOMAIN_NAME : PRO_DOMAIN_NAME}api/courses`, {
        headers: token ? { Authorization: `${token}` } : {},
      })
      .then((res) => {
        const coursesObject = res.data.courses;
        const coursesArray = Object.entries(coursesObject).map(([course_ID, course]: any) => ({
          course_ID,
          ...course,
        }));
        setCourses(coursesArray);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to fetch courses:', err);
        setLoading(false);
      });
  };

  useEffect(() => {
    console.log('ENV', ENV_MODE, DEV_DOMAIN_NAME, PRO_DOMAIN_NAME);
    fetchCourses();
  }, []);

  useEffect(() => {
    const handleTokenChange = () => {
      fetchCourses();
    };

    window.addEventListener('tokenChange', handleTokenChange);

    return () => {
      window.removeEventListener('tokenChange', handleTokenChange);
    };
  }, []);

  if (loading) {
    return <div className="text-center mt-10 text-lg font-semibold">Loading courses...</div>;
  }

  return (
    <div className="grid gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 p-4">
      {courses.map((course) => (
        <Card key={course.course_ID} className="rounded-2xl shadow-md overflow-hidden">
          <div className="relative w-full h-48">
            <Image
              src="/courses-placeholder.svg"
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

            {/* ✅ Progress bar if enrolled */}
            {course.enrollment_status !== 'Not Enrolled' && (
              <div>
                <Typography variant="body2" className="mb-1">
                  Progress: {course.my_progress}%
                </Typography>
                <LinearProgress
                variant="determinate"
                value={course.my_progress >= 0 && course.my_progress <= 100 ? course.my_progress : 0}
                sx={{ height: 10, borderRadius: 5 }}
              />
              </div>
            )}

            <Typography
              variant="subtitle1"
              component="p"
              className="text-blue-600 font-semibold"
            >
              ${course.price}
            </Typography>
          </CardContent>

          <CardActions className="p-4">
            <Button
              fullWidth
              variant="contained"
              color={
                course.enrollment_status === 'Not Enrolled' ||
                !localStorage.getItem('token')
                  ? 'primary'
                  : 'success'
              }
              onClick={() => {
                const token = localStorage.getItem('token');
                if (!token) {
                  openModal('login');
                  return;
                }
                if (course.enrollment_status === 'Not Enrolled') {
                  Enroll(course);
                } else {
                  window.open(`/courses/${course.course_ID}`, '_blank');
                }
              }}
            >
              {course.enrollment_status === 'Not Enrolled' ||
              !localStorage.getItem('token')
                ? 'Enroll'
                : 'Open Course'}
            </Button>
          </CardActions>
        </Card>
      ))}
    </div>
  );
};

export default CoursesList;
