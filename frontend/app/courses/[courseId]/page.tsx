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
    <div className="flex h-[92vh]">
      <div className="flex-1 ml-6">
        {/* You can render selected content or a welcome message here */}
        <p className="text-gray-600">Select a chapter to view its contents</p>
      </div>
      <div className="w-80 bg-white shadow-md p-4 overflow-y-scroll h-[92vh]">
        <h2 className="text-xl font-bold mb-4">Chapters</h2>
        {Object.entries(chapters).map(([id, chapter]: any) => (
          <div key={id} className='accordion-row border-2 border-blue-50 bg-white rounded-md p-[2px] mb-5 chapter-tab-item cursor-pointer'>
            <div style={{ direction: "ltr", textAlign: "left" }} className='flex items-center justify-between p-[10px] getChapterItems collapsed'>
              <div className="flex items-center">
                <h6 className='h6 text-black-800 flex items-center gap-x-2"'>
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="19" viewBox="0 0 20 19" fill="none" className="tw-w-5 tw-h-5">
                    <path  d="M4.37625 0.125C2.30937 0.125 0.625 1.80813 0.625 3.875V15.1237C0.625 17.1906 2.30937 18.875 4.37625 18.875H10.6275V0.125H4.37625ZM11.8737 0.125V8.8675H19.375V3.875C19.375 1.80813 17.6925 0.125 15.625 0.125H11.8737ZM11.8737 10.1175V18.875H15.625C17.6925 18.875 19.375 17.1906 19.375 15.1237V10.1175H11.8737Z" fill="#4848ED"></path>
                  </svg>
                  {chapter.title}
                </h6>
                {/* <button
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
                )} */}
              </div>
              <div className='flex items-center'>
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" className="feather feather-loader loader feather-chevron-down text-gray d-none loader-done"><line x1="12" y1="2" x2="12" y2="6"></line><line x1="12" y1="18" x2="12" y2="22"></line><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line><line x1="2" y1="12" x2="6" y2="12"></line><line x1="18" y1="12" x2="22" y2="12"></line><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line></svg>
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" className="feather collapse-chevron-icon text-gray collapsed feather-chevron-down" href="#collapseChapter8550641" aria-controls="collapseChapter8550641" data-parent="#chapterAccordion" role="button" data-toggle="collapse" aria-expanded="false"><polyline points="6 9 12 15 18 9"></polyline></svg>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
