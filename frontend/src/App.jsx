import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./context/AuthContext.jsx";
import AppLayout from "./layouts/AppLayout.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Login from "./pages/Login.jsx";
import MerchantAnalytics from "./pages/MerchantAnalytics.jsx";
import MerchantDetails from "./pages/MerchantDetails.jsx";
import Forecasts from "./pages/Forecasts.jsx";
import LoadingState from "./components/LoadingState.jsx";

function ProtectedLayout() {
  const { user, loading } = useAuth();
  if (loading) return <LoadingState />;
  return user ? <AppLayout /> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<ProtectedLayout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/analytics" element={<MerchantAnalytics />} />
        <Route path="/forecasts" element={<Forecasts />} />
        <Route path="/merchants/:merchantId" element={<MerchantDetails />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
