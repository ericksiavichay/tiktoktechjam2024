import React, { useState, useEffect } from 'react';
import './FrameEditor.css';
import { FaStar } from 'react-icons/fa';

const REMOTE_HOST = process.env.REACT_APP_REMOTE_HOST;
const LOCAL_BACKEND_PORT = process.env.REACT_APP_LOCAL_BACKEND_PORT;
const LOCAL_HOST = process.env.REACT_APP_LOCAL_HOST;

function FrameEditor({ frame, videoURL, setSegURL, setInpaintURL }) {
    const [blendedFrame, setBlendedFrame] = useState(null);
    const [mask, setMask] = useState(null);
    const [inpaintedFrame, setInpaintedFrame] = useState(null);
    const [segmentationPrompt, setSegmentationPrompt] = useState('');
    const [prompt, setPrompt] = useState('');
    const [negativePrompt, setNegativePrompt] = useState('');
    const [guidance, setGuidance] = useState(7.5);
    const [strength, setStrength] = useState(1.0);
    const [iterations, setIterations] = useState(50);
    const [originalDimensions, setOriginalDimensions] = useState({ width: 0, height: 0 });

    const handleImageLoad = (e) => {
        setOriginalDimensions({ width: e.target.naturalWidth, height: e.target.naturalHeight });
    };

    const handleSegmentFrame = async () => {
        const response = await fetch(`${LOCAL_HOST}:${LOCAL_BACKEND_PORT}/segment_frame`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                frame,
                segmentation_prompt: segmentationPrompt,
            }),
        });
        const data = await response.json();
        setBlendedFrame(data.blended_frame);
        setMask(data.mask);
    };

    const handleSegmentVideo = async () => {
        const response = await fetch(`${LOCAL_HOST}:${LOCAL_BACKEND_PORT}/segment_video/${videoURL}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                segmentation_prompt: segmentationPrompt,
            }),
        });
        const data = await response.json();
        setSegURL(data.out_path);
    }

    const handleInpaintVideo = async () => {
        const response = await fetch(`${LOCAL_HOST}:${LOCAL_BACKEND_PORT}/inpaint_video/segmented_${videoURL}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt,
                negative_prompt: negativePrompt,
                guidance: parseFloat(guidance),
                strength: parseFloat(strength),
                iterations: parseInt(iterations),
            }),
        });

        const data = await response.json();
        setInpaintURL(data.out_path);

    }

    return (
        <div className="frame-editor">
            <h2>Initial Movie Frame</h2>

            <div className="prompts">
                <div className="prompt">
                    <label htmlFor="segmentation-prompt">Segmentation Prompt</label>
                    <input
                        id="segmentation-prompt"
                        type="text"
                        value={segmentationPrompt}
                        onChange={(e) => setSegmentationPrompt(e.target.value)}
                    />
                </div>
                <div className="prompt">
                    <label htmlFor="prompt">Inpaint Prompt</label>
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
                <div className="prompt">
                    <label htmlFor="guidance">Guidance</label>
                    <input
                        id="guidance"
                        type="number"
                        value={guidance}
                        onChange={(e) => setGuidance(e.target.value)}
                    />
                </div>
                <div className="prompt">
                    <label htmlFor="strength">Strength</label>
                    <input
                        id="strength"
                        type="number"
                        value={strength}
                        onChange={(e) => setStrength(e.target.value)}
                    />
                </div>
                <div className="prompt">
                    <label htmlFor="iterations">Iterations</label>
                    <input
                        id="iterations"
                        type="number"
                        value={iterations}
                        onChange={(e) => setIterations(e.target.value)}
                    />
                </div>
                <div className="tools">
                    <button className="tool-button" onClick={handleSegmentFrame}>
                        Segment Frame
                    </button>

                    <button className="tool-button" onClick=''>
                        Inpaint Frame
                    </button>

                    <button className="tool-button" onClick={handleSegmentVideo}>
                        Segment Video
                    </button>

                    <button className="tool-button" onClick={handleInpaintVideo}>
                        Inpaint Video
                    </button>
                </div>

            </div>
            <div className="images-container">
                <div className="selected-frame">
                    <img src={`data:image/jpeg;base64,${frame}`} alt="Selected Frame" onLoad={handleImageLoad} />

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
                        <img src={`data:image/png;base64,${inpaintedFrame}`} alt="Inpainted Frame" />
                    </div>
                )}
            </div>
        </div>
    );
}

export default FrameEditor;
