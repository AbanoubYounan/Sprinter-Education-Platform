const express = require('express');
const chatsController = require('../controllers/chatsControllers')
const multer = require('multer');
const verifyToken = require('../utils/verifyToken')
const router = express.Router();
const storage = multer.memoryStorage();
const upload = multer({ storage });

router.get('/', verifyToken.verifyToken, chatsController.getAllSessions)
router.get('/:SessionID', verifyToken.verifyToken, chatsController.GetConversationHistory)
router.post('/', verifyToken.verifyToken, upload.single('uploaded_file'), chatsController.CreateNewMessage);


module.exports = router;


