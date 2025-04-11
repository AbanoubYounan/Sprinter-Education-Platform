'use client';
import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';

export default function CoursePage() {
  const params = useParams();
  const courseId = params.courseId;

  const [chapters, setChapters] = useState<any>({});
  const [chapterContents, setChapterContents] = useState<Record<string, any>>({});
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!courseId || !token) return;
    fetch(`http://127.0.0.1:5000/api/courses/${courseId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `${token}`
        },
      })
      .then(res => res.json())
      .then(data => {
        setChapters(data.Chapters);
        Object.keys(data.Chapters).forEach(chapterId => {
          fetch(`http://127.0.0.1:5000/api/courses/Chapter/${chapterId.split('+')[1]}`, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `${token}`
            },
          })
            .then(res => res.json())
            .then(content => {
              setChapterContents(prev => ({ ...prev, [chapterId]: content.Content }));
            });
        });
      });
  }, [courseId]);

  return (
    <div className="flex min-h-screen p-4">
      <div className="w-80 bg-white border rounded-lg shadow-md p-4 overflow-y-auto h-full">
        <h2 className="text-xl font-bold mb-4">Chapters</h2>
        {Object.entries(chapters).map(([id, chapter]: any) => (
          <div key={id} className="mb-2">
            <button
              className="w-full text-left font-semibold text-indigo-600 hover:underline"
              onClick={() => setExpanded(expanded === id ? null : id)}
            >
              {chapter.title}
            </button>
            {expanded === id && (
              <ul className="mt-2 ml-4 text-sm text-gray-700">
                {chapterContents[id] &&
                  Object.entries(chapterContents[id])
                    .sort(([, a]: any, [, b]: any) => a.position - b.position)
                    .map(([contentId, content]: any) => (
                      <li key={contentId} className="mb-1">
                        <span className="block font-medium">{content.content_type.toUpperCase()}</span>
                        <span>{content.description.slice(0, 50)}...</span>
                      </li>
                    ))}
              </ul>
            )}
          </div>
        ))}
      </div>
      <div className="flex-1 ml-6">
        {/* You can render selected content or a welcome message here */}
        <p className="text-gray-600">Select a chapter to view its contents</p>
      </div>
    </div>
  );
}
