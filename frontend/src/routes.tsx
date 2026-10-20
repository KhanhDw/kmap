import { createBrowserRouter, RouterProvider } from "react-router-dom";
import AdminDashboard from "./pages/admin/Dashboard";
import Home from "./pages/Home";

const router = createBrowserRouter([
  { path: "/", element: <Home /> },
  { path: "/admin", element: <AdminDashboard /> },
]);

export default function Routes() {
  return <RouterProvider router={router} />;
}
