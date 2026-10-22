"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Empty, ErrorBox, Loading, btnCls, btnDanger, cardCls, inputCls } from "@/components/ui";

interface Post {
  id: string;
  title: string;
  body: string;
  author_id: string;
  author_name: string | null;
  created_at: string;
  reactions: Record<string, number>;
  my_reaction: string | null;
}

interface Comment {
  id: string;
  body: string;
  author_id: string;
  author_name: string | null;
  created_at: string;
  reactions: Record<string, number>;
}

export default function PostPage() {
  const { id } = useParams<{ id: string }>();
  const { user, loading } = useAuth();
  const router = useRouter();
  const [post, setPost] = useState<Post | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [error, setError] = useState<unknown>(null);
  const [body, setBody] = useState("");
  const [flagReason, setFlagReason] = useState("");

  async function load() {
    try {
      setPost(await api.get<Post>(`/posts/${id}`));
      setComments(await api.get<Comment[]>(`/posts/${id}/comments`));
    } catch (e) {
      setError(e);
    }
  }

  useEffect(() => {
    if (!loading && !user) router.push("/login");
    if (user) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, user, id]);

  if (loading || !user) return <Loading />;
  if (error) return <ErrorBox error={error} />;
  if (!post) return <Loading />;

  async function comment(e: React.FormEvent) {
    e.preventDefault();
    await api.post(`/posts/${id}/comments`, { body });
    setBody("");
    await load();
  }

  async function react(targetType: string, targetId: string, kind: string) {
    await api.post("/reactions", { target_type: targetType, target_id: targetId, kind });
    await load();
  }

  async function flag() {
    if (!flagReason.trim()) return;
    await api.post("/flags", { target_type: "post", target_id: post!.id, reason: flagReason });
    setFlagReason("");
    alert("Flagged for moderation");
  }

  async function removeComment(cid: string) {
    await api.del(`/comments/${cid}`);
    await load();
  }

  async function removePost() {
    await api.del(`/posts/${post!.id}`);
    router.back();
  }

  const canDeletePost = user.id === post.author_id || user.role === "admin";

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div className={cardCls}>
        <div className="flex items-start justify-between gap-4">
          <h1 className="text-xl font-bold">{post.title}</h1>
          {canDeletePost && (
            <button onClick={removePost} className={btnDanger}>Delete</button>
          )}
        </div>
        <p className="mt-2 whitespace-pre-wrap text-gray-800">{post.body}</p>
        <div className="mt-3 flex items-center gap-3 text-xs text-gray-500">
          <span>{post.author_name}</span>
          <span>{new Date(post.created_at).toLocaleString()}</span>
          <div className="flex gap-2">
            {["like", "insightful", "celebrate"].map((k) => (
              <button key={k} onClick={() => react("post", post.id, k)}
                className="rounded-full border border-gray-300 px-2 py-0.5 hover:bg-gray-50">
                {k} {post.reactions[k] ? `· ${post.reactions[k]}` : ""}
              </button>
            ))}
          </div>
        </div>
        <div className="mt-3 flex gap-2">
          <input className={`${inputCls} max-w-xs`} placeholder="Flag reason…"
            value={flagReason} onChange={(e) => setFlagReason(e.target.value)} />
          <button onClick={flag} className={btnDanger}>Flag</button>
        </div>
      </div>

      <h2 className="font-semibold">{comments.length} comments</h2>
      {comments.length === 0 ? (
        <Empty>No comments yet.</Empty>
      ) : (
        comments.map((c) => (
          <div key={c.id} className={cardCls}>
            <p className="text-sm text-gray-800">{c.body}</p>
            <div className="mt-2 flex items-center gap-3 text-xs text-gray-500">
              <span>{c.author_name}</span>
              <button onClick={() => react("comment", c.id, "like")}
                className="rounded-full border border-gray-300 px-2 py-0.5 hover:bg-gray-50">
                like {c.reactions.like ? `· ${c.reactions.like}` : ""}
              </button>
              {(c.author_id === user.id || user.role === "admin") && (
                <button onClick={() => removeComment(c.id)} className="text-red-600 hover:underline">
                  delete
                </button>
              )}
            </div>
          </div>
        ))
      )}
      <form onSubmit={comment} className={`${cardCls} flex gap-3`}>
        <input className={inputCls} placeholder="Write a comment…" required
          value={body} onChange={(e) => setBody(e.target.value)} />
        <button className={btnCls}>Comment</button>
      </form>
    </div>
  );
}
