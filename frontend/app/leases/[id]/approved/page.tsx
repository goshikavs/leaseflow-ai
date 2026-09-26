import { ApprovedPage } from "@/components/ApprovedPage";

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <ApprovedPage leaseId={id} />;
}
