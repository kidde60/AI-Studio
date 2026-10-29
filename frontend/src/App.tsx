import { BrowserRouter, Route, Routes } from "react-router-dom";

import ProtectedRoute from "./components/ProtectedRoute";
import { AuthProvider } from "./context/AuthContext";

import CreateContent from "./pages/CreateContent";
import ContentResults from "./pages/ContentResults";
import Projects from "./pages/Projects";

import Storyboard from "./pages/Storyboard";

import Auth from "./pages/Auth";
import { AppLayout } from "./components/layout/AppLayout";
import { Dashboard } from "./pages/Dashboard/Dashboard";
import { Settings } from "./pages/Settings/Settings";
import { Templates } from "./pages/Templates/Templates";
import Media from "./pages/Media/Media";
import { Editor } from "./pages/Editor/Editor";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Auth mode="login" />} />
          <Route path="/register" element={<Auth mode="register" />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              <Route path="/" element={<Dashboard />} />
              <Route path="/create" element={<CreateContent />} />
              <Route path="/content-results" element={<ContentResults />} />
              <Route path="/projects" element={<Projects />} />
              <Route path="/templates" element={<Templates />} />
              <Route path="/media" element={<Media />} />
              <Route path="/settings" element={<Settings />} />
              <Route
                path="/storyboard/:storyboardId"
                element={<Storyboard />}
              />
              <Route path="/editor" element={<Editor />} />
            </Route>
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
