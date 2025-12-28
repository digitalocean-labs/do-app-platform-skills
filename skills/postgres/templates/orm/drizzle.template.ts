// ============================================
// Drizzle Configuration for DO Managed Postgres
// ============================================
//
// Replace {APP_NAME} with your app/schema name
//
// Setup:
//   nvm use 20
//   npm install drizzle-orm pg
//   npm install -D drizzle-kit @types/pg

// ============================================
// drizzle.config.ts
// ============================================

import type { Config } from "drizzle-kit";

export default {
  schema: "./src/db/schema.ts",
  out: "./drizzle",
  driver: "pg",
  dbCredentials: {
    connectionString: process.env.DATABASE_URL!,
  },
  schemaFilter: ["{APP_NAME}"],
  verbose: true,
  strict: true,
} satisfies Config;


// ============================================
// src/db/schema.ts
// ============================================

import { 
  pgTable, 
  pgSchema, 
  serial, 
  text, 
  varchar, 
  boolean,
  timestamp,
  integer 
} from "drizzle-orm/pg-core";
import { relations } from "drizzle-orm";

// Define schema
export const appSchema = pgSchema("{APP_NAME}");

// Users table
export const users = appSchema.table("users", {
  id: serial("id").primaryKey(),
  email: varchar("email", { length: 255 }).notNull().unique(),
  name: text("name"),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow(),
  updatedAt: timestamp("updated_at", { withTimezone: true }),
});

// Posts table
export const posts = appSchema.table("posts", {
  id: serial("id").primaryKey(),
  title: varchar("title", { length: 255 }).notNull(),
  content: text("content"),
  published: boolean("published").default(false),
  authorId: integer("author_id").notNull().references(() => users.id),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow(),
  updatedAt: timestamp("updated_at", { withTimezone: true }),
});

// Relations
export const usersRelations = relations(users, ({ many }) => ({
  posts: many(posts),
}));

export const postsRelations = relations(posts, ({ one }) => ({
  author: one(users, {
    fields: [posts.authorId],
    references: [users.id],
  }),
}));

// Type exports
export type User = typeof users.$inferSelect;
export type NewUser = typeof users.$inferInsert;
export type Post = typeof posts.$inferSelect;
export type NewPost = typeof posts.$inferInsert;


// ============================================
// src/db/index.ts
// ============================================

import { drizzle } from "drizzle-orm/node-postgres";
import { Pool } from "pg";
import * as schema from "./schema";

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false },
  max: 10,
});

export const db = drizzle(pool, { schema });


// ============================================
// src/db/migrate.ts
// ============================================

import { drizzle } from "drizzle-orm/node-postgres";
import { migrate } from "drizzle-orm/node-postgres/migrator";
import { Pool } from "pg";

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false },
});

const db = drizzle(pool);

async function main() {
  console.log("Running migrations...");
  await migrate(db, { migrationsFolder: "./drizzle" });
  console.log("Migrations complete!");
  await pool.end();
}

main().catch((err) => {
  console.error("Migration failed!", err);
  process.exit(1);
});


// ============================================
// Usage example
// ============================================

// import { db } from "./db";
// import { users, posts } from "./db/schema";
// import { eq } from "drizzle-orm";
//
// // Insert user
// const [newUser] = await db.insert(users)
//   .values({ email: "test@example.com", name: "Test" })
//   .returning();
//
// // Query with relations
// const usersWithPosts = await db.query.users.findMany({
//   with: { posts: true }
// });


// ============================================
// package.json scripts
// ============================================
// {
//   "scripts": {
//     "db:generate": "drizzle-kit generate:pg",
//     "db:migrate": "tsx src/db/migrate.ts",
//     "db:push": "drizzle-kit push:pg",
//     "db:studio": "drizzle-kit studio"
//   }
// }


// ============================================
// .env
// ============================================
// DATABASE_URL=postgresql://{APP_NAME}_user:PASSWORD@HOST:25060/defaultdb?sslmode=require
