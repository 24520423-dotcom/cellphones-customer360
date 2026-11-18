import Button from "../../components/Button";
import { useAuth } from "../../hooks/useAuth";
import StatusPage from "../StatusPage";

export default function SessionError() {
  const { refreshSession } = useAuth();
  return (
    <StatusPage title="Không thể kiểm tra phiên đăng nhập">
      <Button onClick={refreshSession}>Thử lại</Button>
    </StatusPage>
  );
}
