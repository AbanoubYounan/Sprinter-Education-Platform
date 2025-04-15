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
    form.append('request_data', JSON.stringify(requestData));
    // 3. Send the POST request
    axios.post('https://chat-sprinter.mes-design.com/chat', form, {
        headers: {
        ...form.getHeaders(),
        },
    })
    .then(response => {
        console.log('Response:', response.data);
        return res.status(201).json({ "Message": response.data });
    })
    .catch(error => {
        console.error('Error:', error.response ? error.response.data : error.message);
        return res.status(400).json({ "Message": error.response ? error.response.data : error.message });
    });

  } catch (error) {
    console.log('error in CreateNewMessage controller', error)
    return res.status(500).json({ message: 'Server error', error });
  }
}
