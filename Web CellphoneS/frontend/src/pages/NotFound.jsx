import { Link } from "react-router-dom";
import Loading from "../components/Loading";
import { useAuth } from "../hooks/useAuth";
import StatusPage from "./StatusPage";

export default function NotFound() {
  const { status } = useAuth();
  const signedIn = status === "authenticated";

  return (
    <StatusPage code="404" title="Không tìm thấy trang bạn yêu cầu.">
      {status === "loading" ? <Loading /> : (
        <Link className="crm-action" to={signedIn ? "/dashboard" : "/login"}>
          {signedIn ? "Quay về Dashboard" : "Đăng nhập"}
        </Link>
      )}
    </StatusPage>
  );
}
