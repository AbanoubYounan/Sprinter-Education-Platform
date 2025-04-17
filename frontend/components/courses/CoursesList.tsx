import React, { useEffect, useState } from 'react';
import { useAuthModal } from '@/context/AuthModalContext';
import { motion } from 'framer-motion';
import axios from 'axios';
import {
  Card,
  CardContent,
  CardActions,
  Button,
  Typography,
  Rating,
  LinearProgress,
  Chip,
} from '@mui/material';
import SchoolIcon from '@mui/icons-material/School';
import CategoryIcon from '@mui/icons-material/Category';
import LockIcon from '@mui/icons-material/Lock'; // Add LockIcon
import Image from 'next/image';

const ENV_MODE = process.env.NEXT_PUBLIC_ENV_MODE;
const DEV_DOMAIN_NAME = process.env.NEXT_PUBLIC_DEV_DOMAIN_NAME;
const PRO_DOMAIN_NAME = process.env.NEXT_PUBLIC_PRO_DOMAIN_NAME;

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
  my_progress: number;
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
            headers: { Authorization: `${token}` },
          }
        );

        if (response.status === 201) {
          setCourses((prev) =>
            prev.map((c) =>
              c.course_ID === course.course_ID
                ? { ...c, enrollment_status: 'Active', my_progress: 0 }
                : c
            )
          );
        }
      } catch (error: any) {
        alert(error?.response?.data?.Message || 'Enrollment failed');
      }
    } else {
      window.open(`/courses/${course.course_ID}`, '_blank');
    }
  };

  const fetchCourses = () => {
    const token = localStorage.getItem('token');
    axios
      .get(`${ENV_MODE === 'DEV' ? DEV_DOMAIN_NAME : PRO_DOMAIN_NAME}api/courses`, {
        headers: token ? { Authorization: `${token}` } : {},
      })
      .then((res) => {
        const coursesObj = res.data.courses;
        const coursesArray = Object.entries(coursesObj).map(([course_ID, course]: any) => ({
          course_ID,
          ...course,
        }));
        setCourses(coursesArray);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Fetch error:', err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchCourses();
    const handleTokenChange = () => fetchCourses();
    window.addEventListener('tokenChange', handleTokenChange);
    return () => window.removeEventListener('tokenChange', handleTokenChange);
  }, []);

  if (loading) return <div className="text-center mt-10 text-lg font-semibold">Loading...</div>;

  return (
    <div className="grid gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 p-4">
      {courses.map((course) => (
        <motion.div
          key={course.course_ID}
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.98 }}
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="cursor-pointer"
          onClick={() => {
            const token = localStorage.getItem('token');
            if (!token) {
              openModal('login');
              return;
            }
            window.open(`/courses/${course.course_ID}`, '_blank');
          }}
        >
          <Card
            className="rounded-3xl shadow-md hover:shadow-2xl transition-shadow duration-300 border border-gray-100"
            sx={{ position: 'relative', backgroundColor: '#f8fafc' }}
          >
            <div className="relative w-full h-48">
              <Image
                src="/courses-placeholder.svg"
                alt={course.course_title}
                fill
                className="object-cover rounded-t-3xl"
              />
              <Chip
                label={course.enrollment_status}
                sx={{
                  position: 'absolute',
                  top: 10,
                  left: 10,
                  color: '#fff',
                  fontWeight: 600,
                  backgroundColor:
                    course.enrollment_status === 'Completed'
                      ? '#16a34a'
                      : course.enrollment_status === 'Active'
                      ? '#3b82f6'
                      : '#6b7280',
                }}
              />
            </div>

            <CardContent className="space-y-3">
              <Typography variant="h6" component="h2" className="font-bold line-clamp-2">
                {course.course_title}
              </Typography>

              <div className="flex items-center text-sm text-gray-600 gap-2">
                <CategoryIcon fontSize="small" /> {course.category}
              </div>

              <div className="flex items-center text-sm text-gray-600 gap-2">
                <SchoolIcon fontSize="small" /> {course.instructor_name}
              </div>

              <div className="flex items-center gap-2">
                <Rating value={course.average_rating} precision={0.1} readOnly size="small" />
                <span className="text-sm text-gray-500">({course.review_count})</span>
              </div>

              {course.enrollment_status !== 'Not Enrolled' && (
                <div>
                  <Typography variant="body2">Progress: {course.my_progress}%</Typography>
                  <LinearProgress
                    variant="determinate"
                    value={
                      course.my_progress >= 0 && course.my_progress <= 100
                        ? course.my_progress
                        : 0
                    }
                    sx={{ height: 8, borderRadius: 5, backgroundColor: '#e0e7ff' }}
                    color="primary"
                  />
                </div>
              )}

              <Typography variant="subtitle1" className="text-blue-600 font-semibold">
                ${course.price}
              </Typography>
            </CardContent>

            <CardActions className="p-4 pt-0">
              <Button
                fullWidth
                variant="contained"
                sx={{
                  borderRadius: '999px',
                  textTransform: 'none',
                  fontWeight: 600,
                  backgroundColor:
                    course.enrollment_status === 'Not Enrolled' || !localStorage.getItem('token')
                      ? '#3b82f6'
                      : '#16a34a',
                  '&:hover': {
                    backgroundColor:
                      course.enrollment_status === 'Not Enrolled' || !localStorage.getItem('token')
                        ? '#2563eb'
                        : '#15803d',
                  },
                }}
                onClick={(e) => {
                  e.stopPropagation();
                  const token = localStorage.getItem('token');
                  if (!token) {
                    openModal('login');
                    return;
                  }
                  course.enrollment_status === 'Not Enrolled'
                    ? Enroll(course)
                    : window.open(`/courses/${course.course_ID}`, '_blank');
                }}
              >
                {course.enrollment_status === 'Not Enrolled' || !localStorage.getItem('token')
                  ? (
                    <>
                      <LockIcon fontSize="small" className="mr-2" /> Enroll Now
                    </>
                  )
                  : 'Open Course'}
              </Button>
            </CardActions>
          </Card>
        </motion.div>
      ))}
    </div>
  );
};

export default CoursesList;
