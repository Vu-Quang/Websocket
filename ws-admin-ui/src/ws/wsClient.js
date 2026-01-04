let socket = null;

export function connectWS({ token, channel, onMessage, onStatus }) {
    socket = new WebSocket(`ws://localhost:9000/ws?token=${token}`);

    socket.onopen = () => {
        onStatus("connected");
        socket.send(JSON.stringify({
            type: "subscribe",
            channels: channel
        }));
    };

    socket.onmessage = (e) => {
        onMessage(JSON.parse(e.data));
    };

    socket.onclose = () => {
        onStatus("closed");
        socket = null;
    };

    socket.onerror = () => onStatus("error");
}

export function disconnectWS() {
    socket?.close();
}

export function pingWS() {
    socket?.send(JSON.stringify({ type: "ping" }));
}
