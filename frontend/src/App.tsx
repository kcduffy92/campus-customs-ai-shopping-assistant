import { Route, Routes } from "react-router";
import Layout from "./components/Layout.tsx";
import HomePage from "./pages/HomePage.tsx";
import CataloguePage from "./pages/CataloguePage.tsx";
import ProductPage from "./pages/ProductPage.tsx";
import NotFoundPage from "./pages/NotFoundPage.tsx";
import LoginPage from "./pages/LoginPage.tsx";
import RegisterPage from "./pages/RegisterPage.tsx";
import AccountPage from "./pages/AccountPage.tsx";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="shop" element={<CataloguePage />} />
        <Route path="products/:productId" element={<ProductPage />} />
        <Route path="account" element={<AccountPage />} />
        <Route path="account/login" element={<LoginPage />} />
        <Route path="account/register" element={<RegisterPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
