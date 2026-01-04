import { useState } from "react";
import { connectWS, disconnectWS, pingWS } from "./wsClient";

export default function useWebSocket() {
    const [status, setStatus] = useState("idle");
    const [messages, setMessages] = useState([]);

    const connect = (token, channel) => {
        setMessages([]);
        connectWS({
            token,
            channel,
            onStatus: setStatus,
            onMessage: (msg) => {
                setMessages(m => [
                    {
                        time: new Date().toLocaleTimeString(),
                        ...msg
                    },
                    ...m
                ]);
            }
        });
    };

    return {
        status,
        messages,
        connect,
        disconnect: disconnectWS,
        ping: pingWS,
    };
}
