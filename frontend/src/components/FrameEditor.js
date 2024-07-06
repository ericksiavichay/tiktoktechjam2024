import React, { useState, useEffect } from 'react';
import './FrameEditor.css';
import { FaStar } from 'react-icons/fa';

const REMOTE_HOST = process.env.REACT_APP_REMOTE_HOST;

function FrameEditor({ frame }) {
    const [keypoints, setKeypoints] = useState([]);
    const [selectedTool, setSelectedTool] = useState('positive');
    const [blendedFrame, setBlendedFrame] = useState(null);
    const [mask, setMask] = useState(null);
    const [inpaintedFrame, setInpaintedFrame] = useState(null);
    const [prompt, setPrompt] = useState('');
    const [negativePrompt, setNegativePrompt] = useState('');

    const handleMouseClick = (e) => {
        const rect = e.target.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const newKeypoint = {
            type: selectedTool,
            x,
            y,
        };

        setKeypoints([...keypoints, newKeypoint]);
    };

    const handleClearKeypoints = () => {
        setKeypoints([]);
    };

    const handleBackspace = (e) => {
        if (e.key === 'Backspace' && !e.target.matches('input, textarea')) {
            e.preventDefault();
            setKeypoints(keypoints.slice(0, -1));
        }
    };

    useEffect(() => {
        document.addEventListener('keydown', handleBackspace);
        return () => {
            document.removeEventListener('keydown', handleBackspace);
        };
    }, [keypoints]);

    const handleSegmentFrame = async () => {
        try {
            const response = await fetch(`${REMOTE_HOST}/segment_frame`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    frame,  // Ensure frame is a base64 encoded string
                    keypoints: keypoints.map(kp => [kp.x, kp.y]),
                    labels: keypoints.map(kp => (kp.type === 'positive' ? 1 : 0)),
                }),
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            setBlendedFrame(data.blended_frame);
            setMask(data.mask);
        } catch (error) {
            console.error('Error segmenting frame:', error);
        }
    };

    const handleInpaintFrame = async () => {
        try {
            const response = await fetch(`${REMOTE_HOST}/inpaint_frame`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    frame,  // Ensure frame is a base64 encoded string
                    mask,
                    prompt,
                    negativePrompt,
                }),
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            setInpaintedFrame(data.inpainted_frame);
        } catch (error) {
            console.error('Error inpainting frame:', error);
        }
    };

    return (
        <div className="frame-editor">
            <h2>Selected Frame 1/1</h2>
            <div className="tools">
                <button
                    className={`tool-button ${selectedTool === 'positive' ? 'selected' : ''}`}
                    onClick={() => setSelectedTool('positive')}
                >
                    <FaStar color="green" /> Positive Keypoint
                </button>
                <button
                    className={`tool-button ${selectedTool === 'negative' ? 'selected' : ''}`}
                    onClick={() => setSelectedTool('negative')}
                >
                    <FaStar color="red" /> Negative Keypoint
                </button>
                <button className="tool-button" onClick={handleClearKeypoints}>
                    Clear Keypoints
                </button>
                <button className="tool-button" onClick={handleSegmentFrame}>
                    Segment Frame
                </button>
            </div>
            <div className="prompts">
                <div className="prompt">
                    <label htmlFor="prompt">Prompt</label>
                    <input
                        id="prompt"
                        type="text"
                        value={prompt}
                        onChange={(e) => setPrompt(e.target.value)}
                    />
                </div>
                <div className="prompt">
                    <label htmlFor="negative-prompt">Negative Prompt</label>
                    <input
                        id="negative-prompt"
                        type="text"
                        value={negativePrompt}
                        onChange={(e) => setNegativePrompt(e.target.value)}
                    />
                </div>
                <button className="tool-button" onClick={handleInpaintFrame}>
                    Inpaint Frame
                </button>
            </div>
            <div className="images-container">
                <div className="selected-frame" onClick={handleMouseClick}>
                    <img src={`data:image/jpeg;base64,${frame}`} alt="Selected Frame" />
                    {keypoints.map((kp, index) => (
                        <FaStar
                            key={index}
                            className="star-icon"
                            color={kp.type === 'positive' ? 'green' : 'red'}
                            style={{ top: kp.y, left: kp.x }}
                        />
                    ))}
                </div>
                {blendedFrame && (
                    <div className="blended-frame">
                        <img src={`data:image/jpeg;base64,${blendedFrame}`} alt="Blended Frame" />
                    </div>
                )}
                {mask && (
                    <div className="mask-frame">
                        <img src={`data:image/png;base64,${mask}`} alt="Mask" />
                    </div>
                )}
                {inpaintedFrame && (
                    <div className="inpainted-frame">
                        <img src={`data:image/jpeg;base64,${inpaintedFrame}`} alt="Inpainted Frame" />
                    </div>
                )}
            </div>
        </div>
    );
}

export default FrameEditor;
