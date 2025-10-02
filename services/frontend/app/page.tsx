import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { Header, Footer } from '@/components/layout';
import { ArrowRight, Search, MessageSquare, Shield } from 'lucide-react';

export default function HomePage() {
  return (
    <>
      <Header />
      <main className="min-h-screen">
        {/* Hero Section */}
        <section className="container mx-auto px-4 py-16">
          <div className="max-w-4xl mx-auto text-center">
            <h1 className="text-5xl font-bold mb-6">
              Welcome to BD Law Assistant
            </h1>
            <p className="text-xl text-muted-foreground mb-8">
              Your comprehensive AI-powered legal research assistant for Bangladesh laws and regulations
            </p>
            <div className="flex gap-4 justify-center">
              <Link href="/register">
                <Button size="lg">
                  Get Started
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
              <Link href="/login">
                <Button size="lg" variant="outline">
                  Sign In
                </Button>
              </Link>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="container mx-auto px-4 py-16 border-t">
          <h2 className="text-3xl font-bold text-center mb-12">Key Features</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="rounded-full bg-primary/10 w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <Search className="h-8 w-8 text-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Smart Search</h3>
              <p className="text-muted-foreground">
                Search through thousands of Bangladesh laws with AI-powered semantic search
              </p>
            </div>

            <div className="text-center">
              <div className="rounded-full bg-primary/10 w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <MessageSquare className="h-8 w-8 text-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Legal Q&A</h3>
              <p className="text-muted-foreground">
                Ask questions and get instant answers with relevant legal citations
              </p>
            </div>

            <div className="text-center">
              <div className="rounded-full bg-primary/10 w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <Shield className="h-8 w-8 text-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Reliable Sources</h3>
              <p className="text-muted-foreground">
                All information is sourced from official Bangladesh law databases
              </p>
            </div>
          </div>
        </section>

        {/* Statistics */}
        <section className="container mx-auto px-4 py-16 border-t">
          <div className="grid md:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-4xl font-bold text-primary">1,242+</div>
              <p className="text-muted-foreground mt-2">Laws Indexed</p>
            </div>
            <div>
              <div className="text-4xl font-bold text-primary">29,000+</div>
              <p className="text-muted-foreground mt-2">Legal Sections</p>
            </div>
            <div>
              <div className="text-4xl font-bold text-primary">100ms</div>
              <p className="text-muted-foreground mt-2">Search Speed</p>
            </div>
            <div>
              <div className="text-4xl font-bold text-primary">2</div>
              <p className="text-muted-foreground mt-2">Languages</p>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="container mx-auto px-4 py-16">
          <div className="bg-primary rounded-lg p-12 text-center text-primary-foreground">
            <h2 className="text-3xl font-bold mb-4">
              Start Your Legal Research Today
            </h2>
            <p className="text-lg mb-8 opacity-90">
              Join thousands of legal professionals using BD Law Assistant
            </p>
            <Link href="/register">
              <Button size="lg" variant="secondary">
                Create Free Account
              </Button>
            </Link>
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}
