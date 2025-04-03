const { SignUp } = require('./create')
const { getUserByEmail } = require('./retrieve')
const { VerifyUser, UpdateEmailVerificationToken } = require('./update')

module.exports = {
    SignUp,
    getUserByEmail,
    VerifyUser,
    UpdateEmailVerificationToken
}