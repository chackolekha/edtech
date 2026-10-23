"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Empty, ErrorBox, Loading, btnCls, cardCls, inputCls } from "@/components/ui";

interface Post {
  id: string;
  title: string;
  body: string;
  author_name: string | null;
  created_at: string;
  comment_count: number;
  reactions: Record<string, number>;
}

export default function CommunityPage() {
  const { id } = useParams<{ id: string }>();
  const { user, loading } = useAuth();
  const router = useRouter();
  const [posts, setPosts] = useState<Post[] | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [member, setMember] = useState(false);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");

  async function load() {
    try {
      setPosts(await api.get<Post[]>(`/communities/${id}/posts`));
      setMember(true);
    } catch (e) {
      setError(e);
      setMember(false);
      setPosts([]);
    }
  }

  useEffect(() => {
    if (!loading && !user) router.push("/login");
    if (user) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, user, id]);

  if (loading || !user) return <Loading />;

  async function join() {
    await api.post(`/communities/${id}/join`);
    await load();
  }

  async function createPost(e: React.FormEvent) {
    e.preventDefault();
    await api.post(`/communities/${id}/posts`, { title, body });
    setTitle("");
    setBody("");
    await load();
  }

  async function react(postId: string, kind: string) {
    await api.post("/reactions", { target_type: "post", target_id: postId, kind });
    await load();
  }

  return (
    <div className="space-y-4">
      <ErrorBox error={!member ? error : null} />
      {!member ? (
        <Empty>
          <p>You must join this community to view and post.</p>
          <button onClick={join} className={`${btnCls} mt-3`}>Join community</button>
        </Empty>
      ) : (
        <>
          <form onSubmit={createPost} className={`${cardCls} space-y-3`}>
            <input className={inputCls} placeholder="Post title" required value={title}
              onChange={(e) => setTitle(e.target.value)} />
            <textarea className={inputCls} rows={3} placeholder="What's on your mind?"
              required value={body} onChange={(e) => setBody(e.target.value)} />
            <button className={btnCls}>Post</button>
          </form>
          {posts === null ? (
            <Loading />
          ) : posts.length === 0 ? (
            <Empty>No posts yet — start the discussion.</Empty>
          ) : (
            posts.map((p) => (
              <div key={p.id} className={cardCls}>
                <Link href={`/posts/${p.id}`} className="font-semibold text-accent hover:underline">
                  {p.title}
                </Link>
                <p className="mt-1 line-clamp-2 text-sm text-gray-600">{p.body}</p>
                <div className="mt-3 flex items-center gap-3 text-xs text-gray-500">
                  <span>{p.author_name ?? "unknown"}</span>
                  <span>{new Date(p.created_at).toLocaleDateString()}</span>
                  <span>{p.comment_count} comments</span>
                  <div className="flex gap-2">
                    {["like", "insightful", "celebrate"].map((k) => (
                      <button key={k} onClick={() => react(p.id, k)}
                        className="rounded-full border border-gray-300 px-2 py-0.5 hover:bg-gray-50">
                        {k} {p.reactions[k] ? `· ${p.reactions[k]}` : ""}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ))
          )}
        </>
      )}
    </div>
  );
}
