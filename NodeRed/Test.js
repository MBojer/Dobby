

var on = msg.payload[0].on

if (msg.payload == "true" ) {
    msg.payload = true;
}

else if (msg.payload == "false" ) {
    msg.payload = false;
}



var on = msg.payload[0].on

msg.payload = { online: true, on: true, brightness: Number(msg.payload) }


// on: true
// brightness: 90

msg.payload = { online: true, on: on, brightness }


return msg;

return msg;