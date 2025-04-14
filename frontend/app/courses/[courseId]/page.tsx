'use client';
/* eslint-disable  @typescript-eslint/no-explicit-any */
import VideoLibraryIcon from '@mui/icons-material/VideoLibrary';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import MenuBookIcon from '@mui/icons-material/MenuBook';
const ENV_MODE = process.env.NEXT_PUBLIC_ENV_MODE
const DEV_DOMAIN_NAME = process.env.NEXT_PUBLIC_DEV_DOMAIN_NAME
const PRO_DOMAIN_NAME = process.env.NEXT_PUBLIC_PRO_DOMAIN_NAME

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';

export default function CoursePage() {
  const params = useParams();
  const courseId = params.courseId;

  const [chapters, setChapters] = useState<any>({});
  const [chapterContent, setChapterContent] = useState<{ [key: string]: any }>({});
  const [expandedChapters, setExpandedChapters] = useState<{ [key: string]: boolean }>({});
  const [selectedLesson, setSelectedLesson] = useState<any>(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!courseId || !token) return;
    fetch(`${ENV_MODE=='DEV'?DEV_DOMAIN_NAME:PRO_DOMAIN_NAME}api/courses/${courseId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `${token}`
        },
      })
      .then(res => res.json())
      .then(data => {
        setChapters(data.Chapters);
      });
  }, [courseId]);

  const handleChapterClick = async (chapterId: string) => {
    const chapterKey = chapterId.split('+')[1];
  
    if (!expandedChapters[chapterId]) {
      if (!chapterContent[chapterId]) {
        try {
          const token = localStorage.getItem('token');
          const res = await fetch(`${ENV_MODE=='DEV'?DEV_DOMAIN_NAME:PRO_DOMAIN_NAME}api/courses/Chapter/${chapterKey}`, {
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `${token}`
            }
          });
          const data = await res.json();
          setChapterContent(prev => ({ ...prev, [chapterId]: data.Content }));
        } catch (err) {
          console.error("Failed to load content:", err);
        }
      }
    }
  
    setExpandedChapters(prev => ({ ...prev, [chapterId]: !prev[chapterId] }));
  };

  const getYouTubeEmbedUrl = (url: string) => {
    const videoIdMatch = url.match(/(?:v=|\/embed\/)([^&?/]+)/);
    const videoId = videoIdMatch ? videoIdMatch[1] : null;
    return videoId ? `https://www.youtube.com/embed/${videoId}` : null;
  };
  
  return (
    <div className="flex h-[92vh]">
      <div className="flex-1 ml-6 p-4 border rounded bg-white shadow-sm">
        {!selectedLesson ? (
          <p className="text-gray-600">Select a chapter to view its contents</p>
        ) : selectedLesson.content_type === 'video' ? (
          <div className="w-full aspect-video">
            <iframe
              className="w-full h-full rounded border-0"
              src={getYouTubeEmbedUrl(selectedLesson.content_url) || ''}
              title="YouTube video player"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            ></iframe>
          </div>
        ) : (
          <iframe
            src={selectedLesson.content_url}
            className="w-full h-[600px] rounded border-0"
            title="PDF Viewer"
          ></iframe>
        )}
      </div>

      <div className="w-80 bg-white shadow-md p-4 overflow-y-scroll h-[92vh]">
        <h2 className="text-xl font-bold mb-4">Chapters</h2>
        {Object.entries(chapters).map(([id, chapter]: any) => (
          <div
            key={id}
            className="accordion-row border-2 border-blue-50 bg-white rounded-md p-[2px] mb-5 chapter-tab-item cursor-pointer"
          >
            <div
              onClick={() => handleChapterClick(id)}
              className="flex items-center justify-between p-[10px] getChapterItems"
            >
              <div className="flex items-center gap-2">
                <MenuBookIcon className="text-indigo-600" />
                <h6 className="font-semibold text-gray-800">{chapter.title}</h6>
              </div>

              {/* Toggle Icon */}
              {expandedChapters[id] ? (
                <ExpandLessIcon className="text-gray-500" />
              ) : (
                <ExpandMoreIcon className="text-gray-500" />
              )}
            </div>

            {/* Show lessons if expanded */}
            {expandedChapters[id] && chapterContent[id] && (
              <div className="pl-6 pt-2">
                {Object.entries(chapterContent[id]).map(([lessonId, lesson]: any) => (
                  <div
                    key={lessonId}
                    className="flex items-center justify-between p-2 bg-gray-100 rounded mb-2"
                    onClick={() => setSelectedLesson(lesson)}
                  >
                    <div className="flex items-center gap-2">
                      {lesson.content_type === 'video' ? (
                        <VideoLibraryIcon className="text-indigo-600" />
                      ) : (
                        <PictureAsPdfIcon className="text-indigo-600" />
                      )}
                      <span className="font-medium text-gray-800">{lesson.content_title}</span>
                    </div>
                    <span className="text-sm text-gray-600">
                      {lesson.duration} {lesson.duration > 1 ? 'minutes' : 'minute'}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
