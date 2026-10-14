// Staging placeholder: proves the theme, fonts, shadcn and the @contract alias work.
// Replaced by the real router and pages in P2-1.
import fixable from '@contract/fixtures/validate_fixable.json'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

function App() {
  const issue = fixable.issues[0]
  return (
    <div className="min-h-screen">
      <header className="border-b bg-card px-4 py-3 font-semibold text-primary">SevaiCheck</header>
      <main className="mx-auto max-w-md p-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Badge className="bg-warning-soft text-warning">Fixable</Badge>
              <span className="text-sm text-muted-foreground">Checked in {fixable.timings_ms.total / 1000} s</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1">
            <p className="font-tamil text-lg font-semibold">{issue.msg_ta}</p>
            <p className="text-sm text-muted-foreground">{issue.msg_en}</p>
            <Button className="mt-3">Retake</Button>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}

export default App
