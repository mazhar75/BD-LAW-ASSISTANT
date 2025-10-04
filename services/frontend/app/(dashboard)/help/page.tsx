'use client';

import { Card } from '@/components/ui/Card';
import { HelpCircle, Book, MessageCircle, Mail, ExternalLink, Phone, FileQuestion } from 'lucide-react';

export default function HelpPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Help & Support</h1>
        <p className="mt-2 text-muted-foreground">
          Get help using BD Law Assistant
        </p>
      </div>

      {/* Support Options */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="p-6">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-blue-100 rounded-lg">
              <Book className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <h3 className="font-bold text-lg mb-2">Documentation</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Learn how to use all features of BD Law Assistant
              </p>
              <a href="#" className="text-sm text-blue-600 hover:underline flex items-center gap-1">
                View Docs <ExternalLink className="h-3 w-3" />
              </a>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-green-100 rounded-lg">
              <MessageCircle className="h-6 w-6 text-green-600" />
            </div>
            <div>
              <h3 className="font-bold text-lg mb-2">Live Chat</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Chat with our support team for immediate assistance
              </p>
              <a href="#" className="text-sm text-green-600 hover:underline flex items-center gap-1">
                Start Chat <ExternalLink className="h-3 w-3" />
              </a>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-purple-100 rounded-lg">
              <Mail className="h-6 w-6 text-purple-600" />
            </div>
            <div>
              <h3 className="font-bold text-lg mb-2">Email Support</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Send us an email and we&apos;ll respond within 24 hours
              </p>
              <a href="mailto:support@bdlaw.com" className="text-sm text-purple-600 hover:underline flex items-center gap-1">
                support@bdlaw.com <ExternalLink className="h-3 w-3" />
              </a>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-yellow-100 rounded-lg">
              <HelpCircle className="h-6 w-6 text-yellow-600" />
            </div>
            <div>
              <h3 className="font-bold text-lg mb-2">FAQ</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Find answers to commonly asked questions
              </p>
              <a href="#" className="text-sm text-yellow-600 hover:underline flex items-center gap-1">
                View FAQ <ExternalLink className="h-3 w-3" />
              </a>
            </div>
          </div>
        </Card>
      </div>

      {/* Common Questions */}
      <Card className="p-6">
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
          <FileQuestion className="h-5 w-5" />
          Common Questions
        </h2>
        <div className="space-y-4">
          <div className="border-b pb-4">
            <h3 className="font-semibold mb-2">How do I search for legal documents?</h3>
            <p className="text-sm text-muted-foreground">
              Go to the Search Laws page, enter your query in the search box, and choose your preferred search type (semantic, keyword, or hybrid). You can also filter by category and year.
            </p>
          </div>
          <div className="border-b pb-4">
            <h3 className="font-semibold mb-2">How do I bookmark a document?</h3>
            <p className="text-sm text-muted-foreground">
              When viewing search results, click the bookmark icon next to any document. You can access your bookmarks from the Bookmarks page in the sidebar.
            </p>
          </div>
          <div className="border-b pb-4">
            <h3 className="font-semibold mb-2">What&apos;s the difference between search types?</h3>
            <p className="text-sm text-muted-foreground">
              Semantic search understands the meaning of your query, keyword search looks for exact matches, and hybrid search combines both approaches for the best results.
            </p>
          </div>
          <div className="pb-4">
            <h3 className="font-semibold mb-2">How can I ask legal questions?</h3>
            <p className="text-sm text-muted-foreground">
              Use the Chat Q&A feature to ask questions in natural language. Our AI will provide detailed answers with citations from relevant legal documents.
            </p>
          </div>
        </div>
      </Card>

      {/* Contact Information */}
      <Card className="p-6">
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
          <Phone className="h-5 w-5" />
          Contact Information
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="font-semibold mb-2">Email</h3>
            <p className="text-sm text-muted-foreground">support@bdlaw.com</p>
            <p className="text-sm text-muted-foreground">info@bdlaw.com</p>
          </div>
          <div>
            <h3 className="font-semibold mb-2">Support Hours</h3>
            <p className="text-sm text-muted-foreground">Monday - Friday: 9:00 AM - 6:00 PM</p>
            <p className="text-sm text-muted-foreground">Saturday: 10:00 AM - 4:00 PM</p>
          </div>
        </div>
      </Card>
    </div>
  );
}
