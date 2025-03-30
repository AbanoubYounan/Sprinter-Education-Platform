const userModel = require('../models/user/index');
const signCookie = require('../utils/cdnSignCookies')
const { CLOUDFRONT_DOMAIN_NAME_Cookie } = require('../config/index')


exports.login = async (req, res) => {
    const { email, password } = req.body;

    try {
        const token = await userModel.login(email, password);
        const signedCookies = await signCookie();
        Object.entries(signedCookies).forEach(([key, value]) => {
            res.cookie(key, value, {
                domain: CLOUDFRONT_DOMAIN_NAME_Cookie,
                httpOnly: false,
                secure: true,
                sameSite: "None",
              });
        });
        res.status(200).json({ message: 'Login successful', token});
    } catch (error) {
        console.error(error);
        res.status(401).json({ message: error.message });
    }
};

