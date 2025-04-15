const chatsModel = require('../models/chat/index')
const axios = require('axios');
const FormData = require('form-data');

exports.CreateNewMessage = async (req, res) => {
  try {
    const { Message, SessionID } = req.body;
    const { UserID } = req.user;
    const PdfFile = req.file;

    if(!Message || !UserID){
      return res.status(400).json({"Message": "Fields can't be empty."})
    }
    
    const form = new FormData();
    const requestData = {
        user_id: UserID,
        user_input: Message,
    };
    if(SessionID){
        requestData['session_id'] = SessionID
    }
    form.append('request_data', JSON.stringify(requestData));
    if(PdfFile){
        form.append('uploaded_file', PdfFile.buffer, {
            filename: PdfFile.originalname,
            contentType: PdfFile.mimetype,
        });
    }
    // 3. Send the POST request
    const response = await axios.post('https://chat-sprinter.mes-design.com/chat', form, {
        headers: {
        ...form.getHeaders(),
        },
    })
    
    if(!SessionID){
        await chatsModel.CreateNewSeesion(UserID, response.data.session_id, `Chat ${response.data.session_id}`)
    }
    return res.status(201).json({ "Response": response.data.response, "SessionID":  response.data.session_id, "SessionTitle": `Chat ${response.data.session_id}`});

  } catch (error) {
    console.log('error in CreateNewMessage controller', error)
    return res.status(500).json({ message: 'Server error', error });
  }
}

exports.getAllSessions =  async (req, res) => {
    try {
      const { UserID } = req.user;
  
      if(!UserID){
        return res.status(400).json({"Message": "Fields can't be empty."})
      }
      
      const sessions = await chatsModel.GetAllSessions(UserID)
      
      return res.status(201).json({ "sessions": sessions });
  
    } catch (error) {
      console.log('getAllSessions', error)
      return res.status(500).json({ message: 'Server error', error });
    }
}

exports.GetConversationHistory = async (req, res) => {
    try {
      const { SessionID } = req.params;
      const { UserID } = req.user;
  
      if(!SessionID || !UserID){
        return res.status(400).json({"Message": "Fields can't be empty."})
      }
      
      // 3. Send the POST request
      const response = await axios.get(`https://chat-sprinter.mes-design.com/conversation/history?user_id=${UserID}&session_id=${SessionID}`)
      
      return res.status(201).json({ "data": response.data });
  
    } catch (error) {
      console.log('error in CreateNewMessage controller', error)
      return res.status(500).json({ message: 'Server error', error });
    }
}
  