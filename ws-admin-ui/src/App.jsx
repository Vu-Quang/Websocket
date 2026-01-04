import { useState } from "react";
import useWebSocket from "./ws/useWebSocket";

export default function App() {
    const [token, setToken] = useState("");
    const [channel, setChannel] = useState("");
    const { status, messages, connect, disconnect, ping } = useWebSocket();

    return (
        <div className="app">
            <h2>WebSocket Admin UI</h2>

            <div className="status">
                Status: <b>{status}</b>
            </div>

            <input
                placeholder="JWT token"
                value={token}
                onChange={e => setToken(e.target.value)}
            />

            <input
                placeholder="Channel"
                value={channel}
                onChange={e => setChannel(e.target.value)}
            />

            <div className="actions">
                <button onClick={() => connect(token, channel)}>Connect</button>
                <button onClick={disconnect}>Disconnect</button>
                <button onClick={ping}>Ping</button>
            </div>

            <pre className="log">
                {messages.map((m, i) => (
                    <div key={i}>
                        [{m.time}] {JSON.stringify(m)}
                    </div>
                ))}
            </pre>
        </div>
    );
}
