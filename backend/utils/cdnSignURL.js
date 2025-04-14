const { getSignedUrl } = require("@aws-sdk/cloudfront-signer");
const {CLOUDFRONT_DOMAIN_NAME, CLOUDFRONT_KEY_PAIR_ID, CLOUDFRONT_PRIVATE_KEY} = require('../config/index')


async function signURL(objectName){
    url = `${CLOUDFRONT_DOMAIN_NAME}/${objectName}`
    const signedUrl = getSignedUrl({
        url,
        keyPairId: CLOUDFRONT_KEY_PAIR_ID,
        dateLessThan: new Date(Date.now() +  1000 * 60 * 60 * 24),
        privateKey: CLOUDFRONT_PRIVATE_KEY
    });

    return signedUrl
}

module.exports = signURL
