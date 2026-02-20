function createVideoStore() {
    let videoUrl = $state<string | null>(null);
    let videoType = $state<'file' | 'url' | 'stream' | 'rtsp' | null>(null);
    let videoStream = $state<MediaStream | null>(null);

    return {
        get videoUrl() {
            return videoUrl;
        },
        get videoType() {
            return videoType;
        },
        get videoStream() {
            return videoStream;
        },
        setVideoUrl: (url: string | null) => {
            videoUrl = url;
        },
        setVideoType: (type: 'file' | 'url' | 'stream' | 'rtsp' | null) => {
            videoType = type;
        },
        setVideoStream: (stream: MediaStream | null) => {
            videoStream = stream;
        }
    };
}

export const videoStore = createVideoStore();
