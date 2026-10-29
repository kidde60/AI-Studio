# AI Video Studio — Frontend

React + TypeScript + Vite frontend for the AI Video Studio.

## Current implementation

### Functional flow
1. Create Video
2. Enter idea/topic
3. Select content style, platform, duration and target audience
4. Generate AI content
5. Review:
   - Title
   - Hook
   - Script
   - Caption
   - Hashtags
   - CTA
   - Follow-up content ideas
6. Continue to Storyboard
7. Storyboard receives the generated content and creates scene suggestions

## API architecture

The frontend now uses:

`React UI → contentService.ts → API client → FastAPI`

For the current MVP, `contentService.ts` uses a local mock generator so the UI can be tested without a backend.

To connect FastAPI later, change:

```ts
const USE_MOCK_API = true;
```

to:

```ts
const USE_MOCK_API = false;
```

Then set:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

The expected endpoint is:

`POST /api/v1/content/generate`

## Run

```bash
npm install
npm run dev
```

## Next implementation stage

The next backend/frontend integration should add:

- FastAPI project structure
- PostgreSQL connection
- `/content/generate`
- OpenAI provider abstraction
- persistent projects and generated content
- authentication
- async jobs with Redis/Celery
- media search through Pexels/Pixabay
- AI voice generation
- subtitle generation
- FFmpeg video rendering
- editor timeline state
