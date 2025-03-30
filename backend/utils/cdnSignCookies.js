const { CLOUDFRONT_DOMAIN_NAME, CLOUDFRONT_KEY_PAIR_ID, CLOUDFRONT_PRIVATE_KEY } = require('../config/index')
const crypto = require("crypto");


async function signCookie(){
    const expirationTime = Math.floor(Date.now() / 1000) + (3600 * 12); // 12-hour expiry

    const policy = JSON.stringify({
        Statement: [
            {
                Resource: `${CLOUDFRONT_DOMAIN_NAME}/*`,
                Condition: {
                    DateLessThan: { "AWS:EpochTime": expirationTime }
                }
            }
        ]
    });

    // Sign the policy
    const signer = crypto.createSign("RSA-SHA1");
    signer.update(policy);
    const signature = signer.sign(CLOUDFRONT_PRIVATE_KEY, "base64");

    return {
        "CloudFront-Policy": Buffer.from(policy).toString("base64"),
        "CloudFront-Signature": signature,
        "CloudFront-Key-Pair-Id": CLOUDFRONT_KEY_PAIR_ID
    };
}

module.exports = signCookie
