import { useRouter } from "next/router";

const LessonPage = () => {
  const router = useRouter();
  const { programId, chapterId, lessonId } = router.query;

  return (
    <div>
      <h1>Lesson {lessonId}</h1>
      <p>Part of Chapter {chapterId} in Program {programId}</p>
    </div>
  );
};

export default LessonPage;
