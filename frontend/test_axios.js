const axios = require('axios');

async function test() {
    try {
        const res = await axios.get('http://127.0.0.1:8000/api/v1/analytics/dashboard', {
            headers: {
                // I need a token for this. Let's just mock what the response structure is by looking at a public endpoint.
            }
        });
        console.log("Axios response keys:", Object.keys(res));
        console.log("res.data keys:", Object.keys(res.data));
    } catch(e) {
        console.log(e.message);
    }
}
test();
