-- Veridexa AI — skill taxonomy seed
-- ~38 canonical skills across the 9 categories from BLUEPRINT.md Section 2.
-- These are the ONLY canonical names stored. Synonym/alias normalization
-- (e.g. "MySQL" / "Postgres" / "SQL Server" -> "SQL") lives in application
-- code (backend/app/services/skill_engine.py), not as a DB table — the
-- blueprint deliberately avoids a synonym table to keep this a lightweight
-- taxonomy rather than a full ontology.

insert into skills (name, category) values
  -- programming
  ('Python', 'programming'),
  ('JavaScript', 'programming'),
  ('TypeScript', 'programming'),
  ('Java', 'programming'),
  ('R', 'programming'),
  ('Go', 'programming'),
  ('C++', 'programming'),

  -- database
  ('SQL', 'database'),
  ('NoSQL', 'database'),
  ('Database Design', 'database'),

  -- data
  ('Data Analysis', 'data'),
  ('Data Visualization', 'data'),
  ('Data Cleaning', 'data'),
  ('ETL', 'data'),
  ('Excel', 'data'),
  ('Power BI', 'data'),
  ('Tableau', 'data'),
  ('Pandas', 'data'),
  ('NumPy', 'data'),
  ('Statistics', 'data'),
  ('A/B Testing', 'data'),
  ('Hypothesis Testing', 'data'),

  -- ai_ml
  ('Machine Learning', 'ai_ml'),
  ('Deep Learning', 'ai_ml'),
  ('Natural Language Processing', 'ai_ml'),
  ('TensorFlow', 'ai_ml'),
  ('PyTorch', 'ai_ml'),
  ('Scikit-learn', 'ai_ml'),

  -- cloud
  ('AWS', 'cloud'),
  ('Azure', 'cloud'),
  ('GCP', 'cloud'),
  ('Docker', 'cloud'),
  ('Kubernetes', 'cloud'),

  -- business
  ('Business Analysis', 'business'),
  ('Project Management', 'business'),
  ('Stakeholder Management', 'business'),

  -- communication
  ('Communication', 'communication'),
  ('Technical Writing', 'communication'),
  ('Presentation', 'communication'),

  -- problem_solving
  ('Problem Solving', 'problem_solving'),
  ('Critical Thinking', 'problem_solving'),

  -- tools
  ('Git', 'tools'),
  ('API Development', 'tools'),
  ('Testing/QA', 'tools')
on conflict (name) do nothing;
