"use client";

import { motion } from "framer-motion";
import GetStarted from "../components/sections/GetStarted";  // Import GetStarted component
import LearnMore from "../components/sections/LearnMore";    // Import LearnMore component

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-br from-indigo-500 to-blue-600 text-white p-6">
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 1.2 }}
        className="text-center"
      >
        {/* Logo with drop shadow and animation */}
        <img
          src="https://sprintscdn.azureedge.net/production/files/174321119867e74abe1c45d.svg"
          alt="Sprints Logo"
          style={{ width: "120px", height: "32px" }} // Logo style for proper size
          className="mx-auto mb-6 drop-shadow-2xl"
        />

        {/* Heading with a more impactful font and color */}
        <motion.h1
          initial={{ opacity: 0, y: -40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.5 }}
          className="text-5xl md:text-6xl font-extrabold mb-6 tracking-tight text-yellow-200"
        >
          Welcome to Sprinter Education Platform
        </motion.h1>

        {/* Subtext with smoother transitions */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 1 }}
          className="text-lg md:text-xl text-gray-200 max-w-2xl mx-auto mb-8 opacity-80"
        >
          Accelerate your learning journey with expert-led courses, personalized pathways, and collaborative projects. Unlock your potential with us!
        </motion.p>

        {/* Get Started and Learn More Buttons */}
        <div className="flex space-x-6 mt-8 justify-center">
          <motion.div
            whileHover={{
              scale: 1.1,
              rotate: -5,
              backgroundPosition: "right center",
            }}
            transition={{
              duration: 0.4,
              type: "spring",
              stiffness: 300,
              damping: 20,
            }}
          >
            <button className="px-8 py-3 text-lg font-semibold text-white bg-gradient-to-br from-pink-500 to-yellow-400 rounded-lg shadow-lg transform hover:scale-110 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500 transition-all ease-in-out">
              Get Started
            </button>
          </motion.div>
          <motion.div
            whileHover={{
              scale: 1.1,
              rotate: 5,
              backgroundPosition: "right center",
            }}
            transition={{
              duration: 0.4,
              type: "spring",
              stiffness: 300,
              damping: 20,
            }}
          >
            <button className="px-8 py-3 text-lg font-semibold text-white bg-gradient-to-br from-teal-500 to-blue-400 rounded-lg shadow-lg transform hover:scale-110 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all ease-in-out">
              Learn More
            </button>
          </motion.div>
        </div>
        
      </motion.div>
      {/* Footer with animation for additional interactive effect */}
      <motion.footer
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1.5, delay: 2 }}
        className="absolute bottom-8 text-center text-gray-400 text-sm"
      >
        <p>&copy; 2025 Sprinter Education. All Rights Reserved.</p>
      </motion.footer>
    </main>
  );
}
